"""Live profile cache — SQLite table for fetched Instagram data."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from ..settings import get_settings
from .accounts_db import get_conn

logger = logging.getLogger(__name__)

ALLOWED_CATEGORIES = {
    "Fitness", "Fashion", "Tech", "Food", "Travel",
    "Lifestyle", "Beauty", "Gaming", "Finance", "Education"
}


# ── Schema ────────────────────────────────────────────────────────────────────

def init_tables() -> None:
    """Create live_profiles table if it doesn't exist, run migrations."""
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS live_profiles (
            account_id        INTEGER PRIMARY KEY,
            username          TEXT,
            biography         TEXT,
            category          TEXT,
            followers_count   INTEGER DEFAULT 0,
            media_count       INTEGER DEFAULT 0,
            avg_likes         REAL DEFAULT 0,
            avg_comments      REAL DEFAULT 0,
            engagement_rate   REAL DEFAULT 0,
            posting_frequency REAL,
            posts_used        INTEGER DEFAULT 0,
            warnings_json     TEXT DEFAULT '[]',
            fetched_at        TEXT NOT NULL,
            raw_json          TEXT,
            FOREIGN KEY (account_id) REFERENCES connected_accounts(id) ON DELETE CASCADE
        )
    """)
    # Migration: add source, data_quality_json, and update unique constraint
    try:
        conn.execute("ALTER TABLE live_profiles ADD COLUMN source TEXT NOT NULL DEFAULT 'official'")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE live_profiles ADD COLUMN data_quality_json TEXT")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE live_profiles ADD COLUMN collected_at TEXT")
    except Exception:
        pass
    try:
        conn.execute("ALTER TABLE live_profiles ADD COLUMN collected_note TEXT")
    except Exception:
        pass
    try:
        # SQLite doesn't support adding constraints easily, so we just add a unique index
        # We also need to handle that account_id is PRIMARY KEY, so we might have rows without account_id?
        # The prompt says: "Make username + source unique together, so the same username can exist once per source."
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_live_profiles_username_source ON live_profiles(username, source)")
    except Exception:
        pass

    conn.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT NOT NULL,
            category        TEXT NOT NULL,
            added_at        TEXT NOT NULL,
            last_status     TEXT,
            last_error      TEXT,
            last_fetched_at TEXT,
            UNIQUE(username, category)
        )
    """)
    conn.commit()
    logger.info("✅ live_profiles and watchlist tables ready")


# ── CRUD ──────────────────────────────────────────────────────────────────────

def upsert_profile(account_id: int | None, data: dict[str, Any], category: str | None = None, source: str = "official") -> dict[str, Any]:
    """Insert or update a live profile cache entry."""
    conn = get_conn()
    now = datetime.now(timezone.utc).isoformat()
    
    params = {
        "account_id": account_id,
        "username": data.get("username"),
        "biography": data.get("biography"),
        "category": category,
        "followers_count": data.get("followers_count", 0),
        "media_count": data.get("media_count", 0),
        "avg_likes": data.get("avg_likes", 0.0),
        "avg_comments": data.get("avg_comments", 0.0),
        "engagement_rate": data.get("engagement_rate", 0.0),
        "posting_frequency": data.get("posting_frequency", None),
        "posts_used": data.get("posts_used", 0),
        "warnings_json": json.dumps(data.get("warnings", [])),
        "fetched_at": data.get("fetched_at") or now,
        "raw_json": json.dumps(data.get("raw_json", {})),
        "source": source,
        "data_quality_json": json.dumps(data.get("data_quality", {})),
        "collected_at": data.get("collected_at", None),
        "collected_note": data.get("collected_note", None),
    }

    if account_id is not None:
        conn.execute(
            """
            INSERT INTO live_profiles
                (account_id, username, biography, category, followers_count, media_count,
                 avg_likes, avg_comments, engagement_rate, posting_frequency,
                 posts_used, warnings_json, fetched_at, raw_json, source, data_quality_json,
                 collected_at, collected_note)
            VALUES (:account_id, :username, :biography, :category, :followers_count, :media_count,
                 :avg_likes, :avg_comments, :engagement_rate, :posting_frequency,
                 :posts_used, :warnings_json, :fetched_at, :raw_json, :source, :data_quality_json,
                 :collected_at, :collected_note)
            ON CONFLICT(account_id) DO UPDATE SET
                username = excluded.username,
                biography = excluded.biography,
                category = COALESCE(excluded.category, live_profiles.category),
                followers_count = excluded.followers_count,
                media_count = excluded.media_count,
                avg_likes = excluded.avg_likes,
                avg_comments = excluded.avg_comments,
                engagement_rate = excluded.engagement_rate,
                posting_frequency = excluded.posting_frequency,
                posts_used = excluded.posts_used,
                warnings_json = excluded.warnings_json,
                fetched_at = excluded.fetched_at,
                raw_json = excluded.raw_json,
                source = excluded.source,
                data_quality_json = excluded.data_quality_json,
                collected_at = excluded.collected_at,
                collected_note = excluded.collected_note
            """,
            params
        )
    else:
        # Upsert by username + source
        conn.execute(
            """
            INSERT INTO live_profiles
                (username, biography, category, followers_count, media_count,
                 avg_likes, avg_comments, engagement_rate, posting_frequency,
                 posts_used, warnings_json, fetched_at, raw_json, source, data_quality_json,
                 collected_at, collected_note)
            VALUES (:username, :biography, :category, :followers_count, :media_count,
                 :avg_likes, :avg_comments, :engagement_rate, :posting_frequency,
                 :posts_used, :warnings_json, :fetched_at, :raw_json, :source, :data_quality_json,
                 :collected_at, :collected_note)
            ON CONFLICT(username, source) DO UPDATE SET
                biography = excluded.biography,
                category = COALESCE(excluded.category, live_profiles.category),
                followers_count = excluded.followers_count,
                media_count = excluded.media_count,
                avg_likes = excluded.avg_likes,
                avg_comments = excluded.avg_comments,
                engagement_rate = excluded.engagement_rate,
                posting_frequency = excluded.posting_frequency,
                posts_used = excluded.posts_used,
                warnings_json = excluded.warnings_json,
                fetched_at = excluded.fetched_at,
                raw_json = excluded.raw_json,
                data_quality_json = excluded.data_quality_json,
                collected_at = excluded.collected_at,
                collected_note = excluded.collected_note
            """,
            params
        )
    conn.commit()
    return get_profile_by_username_and_source(params["username"], source) if params["username"] else {}


def get_profile(account_id: int) -> dict[str, Any] | None:
    conn = get_conn()
    row = conn.execute(
        """SELECT account_id, username, biography, category,
                  followers_count, media_count, avg_likes, avg_comments,
                  engagement_rate, posting_frequency, posts_used,
                  warnings_json, fetched_at, raw_json, source, data_quality_json,
                  collected_at, collected_note
           FROM live_profiles WHERE account_id = ?""",
        (account_id,),
    ).fetchone()
    if not row:
        return None
    return _parse_row(row)

def get_profile_by_username_and_source(username: str, source: str) -> dict[str, Any] | None:
    conn = get_conn()
    row = conn.execute(
        """SELECT account_id, username, biography, category,
                  followers_count, media_count, avg_likes, avg_comments,
                  engagement_rate, posting_frequency, posts_used,
                  warnings_json, fetched_at, raw_json, source, data_quality_json,
                  collected_at, collected_note
           FROM live_profiles WHERE username = ? AND source = ?""",
        (username, source),
    ).fetchone()
    if not row:
        return None
    return _parse_row(row)

def _parse_row(row) -> dict[str, Any]:
    d = dict(row)
    d["warnings"] = json.loads(d.pop("warnings_json", "[]"))
    d["raw_json"] = json.loads(d.pop("raw_json", "{}"))
    data_quality = d.pop("data_quality_json", None)
    if data_quality:
        d["data_quality"] = json.loads(data_quality)
    return d


def list_profiles(category: str | None = None) -> list[dict[str, Any]]:
    conn = get_conn()
    sql = """SELECT account_id, username, biography, category,
                    followers_count, media_count, avg_likes, avg_comments,
                    engagement_rate, posting_frequency, posts_used,
                    warnings_json, fetched_at, source, data_quality_json,
                    collected_at, collected_note
             FROM live_profiles"""
    params: list[Any] = []
    if category:
        sql += " WHERE category = ?"
        params.append(category)
    sql += " ORDER BY fetched_at DESC"
    rows = conn.execute(sql, params).fetchall()
    return [_parse_row(r) for r in rows]


def is_stale(account_id: int | None = None, username: str | None = None, source: str = "official", ttl_hours: int | None = None) -> bool:
    """Return True if the cache is missing or older than TTL."""
    if ttl_hours is None:
        ttl_hours = get_settings().CACHE_TTL_HOURS
    conn = get_conn()
    if account_id is not None:
        row = conn.execute("SELECT fetched_at FROM live_profiles WHERE account_id = ?", (account_id,)).fetchone()
    elif username is not None:
        row = conn.execute("SELECT fetched_at FROM live_profiles WHERE username = ? AND source = ?", (username, source)).fetchone()
    else:
        return True

    if not row:
        return True
    try:
        fetched = datetime.fromisoformat(row["fetched_at"])
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - fetched > timedelta(hours=ttl_hours)
    except (ValueError, TypeError):
        return True

def delete_profile(account_id: int) -> bool:
    conn = get_conn()
    cur = conn.execute("DELETE FROM live_profiles WHERE account_id = ?", (account_id,))
    conn.commit()
    return cur.rowcount > 0

def get_cache_counts_by_source() -> dict[str, int]:
    conn = get_conn()
    rows = conn.execute("SELECT source, COUNT(*) as cnt FROM live_profiles GROUP BY source").fetchall()
    return {r["source"]: r["cnt"] for r in rows}

# ── Watchlist ────────────────────────────────────────────────────────────────
def add_to_watchlist(username: str, category: str) -> bool:
    username = username.lower().lstrip("@")
    conn = get_conn()
    now = datetime.now(timezone.utc).isoformat()
    try:
        conn.execute(
            "INSERT INTO watchlist (username, category, added_at, last_status) VALUES (?, ?, ?, ?)",
            (username, category, now, "added")
        )
        conn.commit()
        return True
    except Exception:
        return False

def remove_from_watchlist(item_id: int) -> bool:
    conn = get_conn()
    cur = conn.execute("DELETE FROM watchlist WHERE id = ?", (item_id,))
    conn.commit()
    return cur.rowcount > 0

def list_watchlist(category: str | None = None) -> list[dict[str, Any]]:
    conn = get_conn()
    sql = "SELECT id, username, category, added_at, last_status, last_error, last_fetched_at FROM watchlist"
    params = []
    if category:
        sql += " WHERE category = ?"
        params.append(category)
    sql += " ORDER BY added_at DESC"
    return [dict(r) for r in conn.execute(sql, params).fetchall()]

def update_watchlist_status(username: str, category: str, status: str, error: str | None = None):
    conn = get_conn()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE watchlist SET last_status = ?, last_error = ?, last_fetched_at = ? WHERE username = ? AND category = ?",
        (status, error, now, username, category)
    )
    conn.commit()
