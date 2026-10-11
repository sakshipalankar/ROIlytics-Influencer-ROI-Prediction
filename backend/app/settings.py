"""Centralised settings — reads .env once and exposes typed config."""
from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv

# Load .env from project root (two levels up from backend/app/)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(Path(__file__).resolve().parents[1] / ".env")  # backend/.env
load_dotenv(PROJECT_ROOT / ".env")  # optional fallback, never overrides


class Settings:
    """Plain-object settings parsed from environment variables."""

    # Instagram
    INSTAGRAM_API_BASE: str = os.getenv("INSTAGRAM_API_BASE", "https://graph.instagram.com")
    INSTAGRAM_APP_ID: str = os.getenv("INSTAGRAM_APP_ID", "")
    INSTAGRAM_APP_SECRET: str = os.getenv("INSTAGRAM_APP_SECRET", "")

    # Token encryption
    TOKEN_ENCRYPTION_KEY: str = os.getenv("TOKEN_ENCRYPTION_KEY", "")

    # Cache
    CACHE_TTL_HOURS: int = int(os.getenv("CACHE_TTL_HOURS", "6"))

    # Feature flags
    ENABLE_BUSINESS_DISCOVERY: bool = os.getenv("ENABLE_BUSINESS_DISCOVERY", "false").lower() == "true"
    ENABLE_PUBLIC_LOOKUP: bool = os.getenv("ENABLE_PUBLIC_LOOKUP", "false").lower() == "true"
    PLAYWRIGHT_HEADLESS: bool = os.getenv("PLAYWRIGHT_HEADLESS", "false").lower() == "true"
    SAVE_DEBUG_HTML: bool = os.getenv("SAVE_DEBUG_HTML", "false").lower() == "true"

    # Public Lookup Constraints
    PUBLIC_LOOKUP_MIN_DELAY_SEC: int = int(os.getenv("PUBLIC_LOOKUP_MIN_DELAY_SEC", "8"))
    PUBLIC_LOOKUP_MAX_PER_HOUR: int = int(os.getenv("PUBLIC_LOOKUP_MAX_PER_HOUR", "20"))
    PUBLIC_LOOKUP_TIMEOUT_SEC: int = int(os.getenv("PUBLIC_LOOKUP_TIMEOUT_SEC", "45"))
    PUBLIC_LOOKUP_MAX_FAILURES: int = int(os.getenv("PUBLIC_LOOKUP_MAX_FAILURES", "3"))
    PUBLIC_LOOKUP_COOLDOWN_MIN: int = int(os.getenv("PUBLIC_LOOKUP_COOLDOWN_MIN", "30"))
    PUBLIC_LOOKUP_CACHE_TTL_HOURS: int = int(os.getenv("PUBLIC_LOOKUP_CACHE_TTL_HOURS", "24"))

    # Reliability logic thresholds
    RELIABLE_MIN_FOLLOWERS: int = int(os.getenv("RELIABLE_MIN_FOLLOWERS", "100"))
    RELIABLE_MIN_POSTS: int = int(os.getenv("RELIABLE_MIN_POSTS", "3"))

    # Paths
    PROJECT_ROOT: Path = PROJECT_ROOT
    DATA_DIR: Path = PROJECT_ROOT / "data"
    LIVE_CACHE_DB: Path = PROJECT_ROOT / "data" / "live_cache.db"
    MODEL_PATH: Path = PROJECT_ROOT / "models" / "best_model.pkl"
    RESULTS_PATH: Path = PROJECT_ROOT / "models" / "model_results.json"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
