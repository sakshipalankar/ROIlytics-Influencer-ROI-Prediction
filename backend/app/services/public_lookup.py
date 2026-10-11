"""Public Lookup service using Playwright Chromium."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import TypedDict, Optional, List, Dict, Any, Protocol
from statistics import mean
from fastapi import HTTPException
import os
import importlib

from ..settings import get_settings

logger = logging.getLogger(__name__)


class RawPost(TypedDict):
    like_count: Optional[int]
    comments_count: Optional[int]
    timestamp: Optional[str]


class RawPublicProfile(TypedDict):
    username: str
    followers_count: Optional[int]
    media_count: Optional[int]
    biography: Optional[str]
    posts: List[RawPost]


# Global locks and state for in-process rate limiting and safety
_lock = asyncio.Lock()
_last_fetch_time = 0.0
_hourly_fetches: list[float] = []
_consecutive_failures = 0
_circuit_breaker_until: Optional[float] = None


class PageReaderNotImplemented(Exception):
    pass

class PageReader(Protocol):
    async def read(self, page: Any, username: str) -> RawPublicProfile: ...

class NotImplementedReader:
    async def read(self, page: Any, username: str) -> RawPublicProfile:
        raise PageReaderNotImplemented("Page reader not implemented yet")

_reader_instance: PageReader = NotImplementedReader()
_reader_name: str = "NotImplementedReader"
_reader_implemented: bool = False

def _init_reader():
    global _reader_instance, _reader_name, _reader_implemented
    reader_path = os.getenv("PUBLIC_LOOKUP_READER")
    if not reader_path:
        return
    try:
        mod_path, class_name = reader_path.split(":")
        mod = importlib.import_module(mod_path)
        cls = getattr(mod, class_name)
        _reader_instance = cls()
        _reader_name = class_name
        _reader_implemented = True
    except Exception as e:
        logger.warning(f"Failed to load PUBLIC_LOOKUP_READER '{reader_path}': {e}")

_init_reader()


class PublicLookupDisabled(HTTPException):
    def __init__(self):
        super().__init__(status_code=503, detail="Public lookup is disabled")


async def _check_rate_limits() -> None:
    """Enforce circuit breaker, delay, and hourly budgets."""
    global _last_fetch_time, _hourly_fetches, _circuit_breaker_until, _consecutive_failures

    now = datetime.now(timezone.utc).timestamp()
    settings = get_settings()

    if not settings.ENABLE_PUBLIC_LOOKUP:
        raise PublicLookupDisabled()

    if _circuit_breaker_until and now < _circuit_breaker_until:
        raise HTTPException(status_code=503, detail="Public lookup paused to avoid blocking")
    elif _circuit_breaker_until and now >= _circuit_breaker_until:
        # Reset breaker after cooldown
        _circuit_breaker_until = None
        _consecutive_failures = 0

    # Clean old requests from window
    _hourly_fetches = [t for t in _hourly_fetches if now - t < 3600]
    if len(_hourly_fetches) >= settings.PUBLIC_LOOKUP_MAX_PER_HOUR:
        oldest = _hourly_fetches[0]
        wait_sec = 3600 - (now - oldest)
        raise HTTPException(
            status_code=429,
            detail=f"Hourly budget exceeded. Try again in {int(wait_sec)}s",
        )

    time_since_last = now - _last_fetch_time
    if time_since_last < settings.PUBLIC_LOOKUP_MIN_DELAY_SEC:
        await asyncio.sleep(settings.PUBLIC_LOOKUP_MIN_DELAY_SEC - time_since_last)

    _last_fetch_time = datetime.now(timezone.utc).timestamp()
    _hourly_fetches.append(_last_fetch_time)


async def fetch_public_profile(username: str) -> RawPublicProfile:
    global _consecutive_failures, _circuit_breaker_until
    
    settings = get_settings()
    
    async with _lock:
        await _check_rate_limits()

    try:
        from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    except ImportError:
        raise HTTPException(status_code=500, detail="Playwright is not installed.")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=settings.PLAYWRIGHT_HEADLESS)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            url = f"https://www.instagram.com/{username}/"
            response = await page.goto(url, timeout=settings.PUBLIC_LOOKUP_TIMEOUT_SEC * 1000)

            if response and response.status == 404:
                raise HTTPException(status_code=404, detail="Profile not found")

            # Check if we got redirected to a login wall
            if "/accounts/login" in page.url or "/challenge" in page.url:
                raise HTTPException(status_code=429, detail="Blocked, try later (login wall)")

            # Call the user-implemented page reader
            try:
                raw_profile = await _reader_instance.read(page, username)
            except PageReaderNotImplemented as e:
                raise HTTPException(status_code=501, detail=str(e))
                
            # Validate reader output (B2b)
            if raw_profile.get("followers_count") is not None and raw_profile["followers_count"] < 0:
                raise HTTPException(status_code=502, detail="Negative followers_count not allowed")
            if raw_profile.get("media_count") is not None and raw_profile["media_count"] < 0:
                raise HTTPException(status_code=502, detail="Negative media_count not allowed")
            
            now_utc = datetime.now(timezone.utc)
            for p in raw_profile.get("posts", []):
                if p.get("like_count") is not None and p["like_count"] < 0:
                    raise HTTPException(status_code=502, detail="Negative like_count not allowed")
                if p.get("comments_count") is not None and p["comments_count"] < 0:
                    raise HTTPException(status_code=502, detail="Negative comments_count not allowed")
                if p.get("timestamp"):
                    try:
                        dt = datetime.fromisoformat(p["timestamp"].replace("Z", "+00:00"))
                        if dt > now_utc:
                            raise HTTPException(status_code=502, detail="Future timestamp not allowed")
                    except ValueError:
                        pass
            
            # Success, reset consecutive failures
            async with _lock:
                _consecutive_failures = 0
            
            return raw_profile

        except PlaywrightTimeoutError:
            raise HTTPException(status_code=504, detail="Request timed out")
        except HTTPException as e:
            # Re-raise known block/404 exceptions
            if e.status_code == 429:
                async with _lock:
                    _consecutive_failures += 1
                    if _consecutive_failures >= settings.PUBLIC_LOOKUP_MAX_FAILURES:
                        now = datetime.now(timezone.utc).timestamp()
                        _circuit_breaker_until = now + (settings.PUBLIC_LOOKUP_COOLDOWN_MIN * 60)
            raise
        except Exception as e:
            logger.exception("Failed to fetch public profile")
            raise HTTPException(status_code=502, detail="Failed to parse page")
        finally:
            await context.close()
            await browser.close()


def compute_features(raw: RawPublicProfile) -> Dict[str, Any]:
    settings = get_settings()
    posts = raw["posts"]
    
    followers = raw["followers_count"]
    warnings: List[str] = []
    
    if followers is None:
        warnings.append("incomplete_data")
        followers = 0
    elif followers < settings.RELIABLE_MIN_FOLLOWERS:
        warnings.append("low_followers")
        
    posts_used = len(posts)
    if posts_used == 0:
        warnings.append("no_posts")
    elif posts_used < settings.RELIABLE_MIN_POSTS:
        warnings.append("few_posts")
        
    likes = [p["like_count"] for p in posts if p.get("like_count") is not None]
    comments = [p["comments_count"] for p in posts if p.get("comments_count") is not None]

    if len(likes) < posts_used:
        warnings.append("hidden_likes")

    avg_likes = round(mean(likes), 2) if likes else 0.0
    avg_comments = round(mean(comments), 2) if comments else 0.0
    engagement_rate = round((avg_likes + avg_comments) / max(followers, 1), 6)
    
    # Posting frequency: posts per week based on timestamps
    posting_frequency = None
    timestamps = []
    for p in posts:
        ts = p.get("timestamp")
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                timestamps.append(dt)
            except ValueError:
                pass

    if len(timestamps) >= 2:
        timestamps.sort()
        span_days = (timestamps[-1] - timestamps[0]).days
        if span_days > 0:
            posting_frequency = round((len(timestamps) / span_days) * 7.0, 4)
        else:
            posting_frequency = 0.0
            
    return {
        "followers_count": followers if "incomplete_data" not in warnings else None,
        "media_count": raw["media_count"] or 0,
        "avg_likes": avg_likes,
        "avg_comments": avg_comments,
        "engagement_rate": engagement_rate,
        "posting_frequency": posting_frequency,
        "posts_used": posts_used,
        "warnings": warnings,
    }


def get_public_lookup_status() -> dict:
    settings = get_settings()
    now = datetime.now(timezone.utc).timestamp()
    
    from ..services import live_db
    cache_counts = live_db.get_cache_counts_by_source()
    
    return {
        "enabled": settings.ENABLE_PUBLIC_LOOKUP,
        "headless": settings.PLAYWRIGHT_HEADLESS,
        "requests_last_hour": len([t for t in _hourly_fetches if now - t < 3600]),
        "budget_limit": settings.PUBLIC_LOOKUP_MAX_PER_HOUR,
        "paused": _circuit_breaker_until is not None and now < _circuit_breaker_until,
        "paused_until": _circuit_breaker_until,
        "reader_implemented": _reader_implemented,
        "reader_name": _reader_name,
        "cache_counts": cache_counts
    }
