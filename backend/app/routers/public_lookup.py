"""Router for public profile lookup and watchlist."""
from __future__ import annotations

import logging
from typing import List, Any
from fastapi import APIRouter, HTTPException, Query

from ..schemas.schemas import (
    PublicLookupRequest, PublicSnapshotRequest, PublicLookupResponse,
    WatchlistAddRequest, WatchlistRefreshRequest
)
from ..services import live_db
from ..services.predictor import PredictorService
from ..services.public_lookup import (
    fetch_public_profile, compute_features, get_public_lookup_status, RawPublicProfile
)
from ..settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/public", tags=["public"])


def _check_enabled():
    if not get_settings().ENABLE_PUBLIC_LOOKUP:
        raise HTTPException(status_code=503, detail="Public lookup is disabled")


def _build_response(username: str, features: dict, category: str, spend: float, fetched_at: str, from_cache: bool, source: str) -> PublicLookupResponse:
    warnings = features.get("warnings", [])
    unreliable_flags = {"low_followers", "few_posts", "no_posts", "incomplete_data"}
    reliable = not bool(unreliable_flags.intersection(warnings))
    
    followers = features.get("followers_count")
    posts_used = features.get("posts_used", 1)  # Default to 1 if missing for safety
    has_no_data = followers is None or followers < 1 or "no_posts" in warnings
    
    if has_no_data:
        reliable = False
        tier = "Insufficient data"
        if followers is None or followers < 1:
            reliability_note = "Follower count is missing or zero. Cannot compute reliable ROI."
        else:
            reliability_note = "Account has no posts. Cannot compute reliable ROI."
        estimated_roi = None
        predicted_revenue = None
        predicted_profit = None
    else:
        svc = PredictorService.get()
        try:
            pred = svc.predict(
                followers_count=followers or 0,
                media_count=features.get("media_count") or 0,
                avg_likes=features.get("avg_likes", 0.0),
                avg_comments=features.get("avg_comments", 0.0),
                category=category,
                posting_frequency=features.get("posting_frequency") or 0.0,
                spend=spend,
            )
            estimated_roi = pred["estimated_roi"]
            predicted_revenue = pred["predicted_revenue"]
            predicted_profit = pred["predicted_profit"]
            tier = pred["tier"]
            reliability_note = None
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Prediction failed: {str(exc)}")

        if not reliable:
            tier = "Insufficient data"
            if "incomplete_data" in warnings:
                reliability_note = "Profile data is incomplete (e.g. missing followers)."
            elif "few_posts" in warnings:
                reliability_note = "Account has very few posts. Engagement metrics may be skewed."
            elif "low_followers" in warnings:
                reliability_note = "Follower count is too low for reliable ROI modeling."

    return PublicLookupResponse(
        profile={
            "username": username,
            "biography": features.get("biography"),
            "category": category,
        },
        features={
            "followers_count": features.get("followers_count") or 0,
            "media_count": features.get("media_count", 0),
            "avg_likes": features.get("avg_likes", 0.0),
            "avg_comments": features.get("avg_comments", 0.0),
            "engagement_rate": features.get("engagement_rate", 0.0),
            "posting_frequency": features.get("posting_frequency"),
        },
        warnings=warnings,
        estimated_roi=estimated_roi,
        tier=tier,
        predicted_revenue=predicted_revenue,
        predicted_profit=predicted_profit,
        fetched_at=fetched_at,
        from_cache=from_cache,
        reliable=reliable,
        reliability_note=reliability_note,
        source=source,
        note="Third-party public data, may be incomplete" if source == "public_lookup" else None
    )


@router.get("/status")
async def get_status():
    return get_public_lookup_status()


@router.post("/lookup", response_model=PublicLookupResponse)
async def public_lookup(
    body: PublicLookupRequest,
    refresh: bool = Query(False)
):
    _check_enabled()
    username = body.username.lower()

    from_cache = False
    profile_data = None
    settings = get_settings()

    if not refresh and not live_db.is_stale(username=username, source="public_lookup", ttl_hours=settings.PUBLIC_LOOKUP_CACHE_TTL_HOURS):
        profile_data = live_db.get_profile_by_username_and_source(username, "public_lookup")
        if profile_data:
            from_cache = True

    if not profile_data:
        raw_profile = await fetch_public_profile(username)
        features = compute_features(raw_profile)
        
        # Save to DB
        data_for_db = {
            "username": raw_profile["username"],
            "biography": raw_profile.get("biography"),
            "followers_count": features["followers_count"],
            "media_count": features["media_count"],
            "avg_likes": features["avg_likes"],
            "avg_comments": features["avg_comments"],
            "engagement_rate": features["engagement_rate"],
            "posting_frequency": features["posting_frequency"],
            "posts_used": features["posts_used"],
            "warnings": features["warnings"],
            "raw_json": raw_profile
        }
        profile_data = live_db.upsert_profile(account_id=None, data=data_for_db, category=body.category, source="public_lookup")

    if not profile_data:
         raise HTTPException(status_code=500, detail="Failed to load profile data")

    # Reconstruct features for predictor
    feats = {
        "followers_count": profile_data.get("followers_count"),
        "media_count": profile_data.get("media_count"),
        "avg_likes": profile_data.get("avg_likes"),
        "avg_comments": profile_data.get("avg_comments"),
        "engagement_rate": profile_data.get("engagement_rate"),
        "posting_frequency": profile_data.get("posting_frequency"),
        "warnings": profile_data.get("warnings", []),
        "biography": profile_data.get("biography")
    }

    return _build_response(
        username=profile_data["username"],
        features=feats,
        category=profile_data["category"],
        spend=body.spend,
        fetched_at=profile_data["fetched_at"],
        from_cache=from_cache,
        source="public_lookup"
    )


@router.post("/snapshot", response_model=PublicLookupResponse)
async def public_snapshot(body: PublicSnapshotRequest):
    # This must work even when ENABLE_PUBLIC_LOOKUP is false
    username = body.username.lower()
    
    raw_profile: RawPublicProfile = {
        "username": username,
        "followers_count": body.followers_count,
        "media_count": body.media_count,
        "biography": body.biography,
        "posts": [p.model_dump() for p in body.posts]
    }
    
    features = compute_features(raw_profile)
    data_for_db = {
        "username": raw_profile["username"],
        "biography": raw_profile.get("biography"),
        "followers_count": features["followers_count"],
        "media_count": features["media_count"],
        "avg_likes": features["avg_likes"],
        "avg_comments": features["avg_comments"],
        "engagement_rate": features["engagement_rate"],
        "posting_frequency": features["posting_frequency"],
        "posts_used": features["posts_used"],
        "warnings": features["warnings"],
        "raw_json": raw_profile,
        "fetched_at": body.collected_at,  # optional override
    }
    profile_data = live_db.upsert_profile(account_id=None, data=data_for_db, category=body.category, source="public_snapshot")
    
    feats = {
        "followers_count": profile_data.get("followers_count"),
        "media_count": profile_data.get("media_count"),
        "avg_likes": profile_data.get("avg_likes"),
        "avg_comments": profile_data.get("avg_comments"),
        "engagement_rate": profile_data.get("engagement_rate"),
        "posting_frequency": profile_data.get("posting_frequency"),
        "warnings": profile_data.get("warnings", []),
        "biography": profile_data.get("biography"),
        "posts_used": profile_data.get("posts_used", 1)
    }

    resp = _build_response(
        username=profile_data["username"],
        features=feats,
        category=profile_data["category"],
        spend=body.spend,
        fetched_at=profile_data["fetched_at"],
        from_cache=False,
        source="public_snapshot"
    )
    
    dt = body.collected_at or profile_data["fetched_at"]
    try:
        from datetime import datetime
        dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        dt_str = dt_obj.strftime("%d %b %Y")
    except Exception:
        dt_str = "Unknown Date"

    if body.collected_note:
        resp.note = f"Manual snapshot, collected from public profile on {dt_str} | {body.collected_note}"
    else:
        resp.note = f"Manual snapshot, collected from public profile on {dt_str}"
    return resp

# ── Watchlist Routes ─────────────────────────────────────────────────────────

@router.get("/watchlist")
async def get_watchlist():
    return live_db.list_watchlist()

@router.post("/watchlist")
async def add_watchlist(body: WatchlistAddRequest):
    success = live_db.add_to_watchlist(body.username, body.category)
    if not success:
        raise HTTPException(status_code=400, detail="Username already in watchlist for this category")
    return {"status": "added"}

@router.delete("/watchlist/{item_id}")
async def delete_watchlist(item_id: int):
    success = live_db.remove_from_watchlist(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return {"status": "deleted"}

@router.post("/refresh-watchlist")
async def refresh_watchlist(body: WatchlistRefreshRequest):
    _check_enabled()
    
    items = live_db.list_watchlist(body.category)
    results = []
    
    for item in items:
        username = item["username"]
        try:
            raw_profile = await fetch_public_profile(username)
            features = compute_features(raw_profile)
            
            data_for_db = {
                "username": raw_profile["username"],
                "biography": raw_profile.get("biography"),
                "followers_count": features["followers_count"],
                "media_count": features["media_count"],
                "avg_likes": features["avg_likes"],
                "avg_comments": features["avg_comments"],
                "engagement_rate": features["engagement_rate"],
                "posting_frequency": features["posting_frequency"],
                "posts_used": features["posts_used"],
                "warnings": features["warnings"],
                "raw_json": raw_profile
            }
            live_db.upsert_profile(account_id=None, data=data_for_db, category=item["category"], source="public_lookup")
            live_db.update_watchlist_status(username, item["category"], "success")
            
            results.append({"username": username, "status": "success", "error": None})
            
        except HTTPException as e:
            if e.status_code == 503:
                # Circuit breaker tripped or service disabled - STOP the run
                live_db.update_watchlist_status(username, item["category"], "paused", str(e.detail))
                results.append({"username": username, "status": "paused", "error": str(e.detail)})
                break
            else:
                live_db.update_watchlist_status(username, item["category"], "error", str(e.detail))
                results.append({"username": username, "status": "error", "error": str(e.detail)})
        except Exception as e:
            live_db.update_watchlist_status(username, item["category"], "error", str(e))
            results.append({"username": username, "status": "error", "error": str(e)})

    return {"results": results}
