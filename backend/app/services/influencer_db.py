"""Influencer database service — user auth and scraped influencers dataset.
"""
from __future__ import annotations

import os
import sqlite3
import logging
from pathlib import Path
from typing import Any, Tuple, List, Optional
from decimal import Decimal

from ..settings import get_settings
from . import live_db

try:
    import pymysql
    import pymysql.cursors
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "data" / "influencers.db"

# MySQL Settings from environment
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "roilytics_db")

from .constants import CATEGORY_ER_BENCHMARKS, BUDGET_TIER_MAP, BRAND_ACCOUNTS

_mysql_failed_logged = False


def get_mysql_conn():
    """Attempt to establish a MySQL connection using PyMySQL."""
    if not PYMYSQL_AVAILABLE:
        return None
    # Re-read env vars in case .env was updated dynamically
    host = os.getenv("MYSQL_HOST", MYSQL_HOST)
    port = int(os.getenv("MYSQL_PORT", str(MYSQL_PORT)))
    user = os.getenv("MYSQL_USER", MYSQL_USER)
    password = os.getenv("MYSQL_PASSWORD", MYSQL_PASSWORD)
    database = os.getenv("MYSQL_DATABASE", MYSQL_DATABASE)

    if not password:
        return None

    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=2,
            read_timeout=5,
            autocommit=True,
        )
        return conn
    except Exception as exc:
        if hasattr(exc, "args") and exc.args and exc.args[0] == 1049:
            try:
                temp_conn = pymysql.connect(
                    host=host, port=port, user=user, password=password,
                    charset="utf8mb4", connect_timeout=2
                )
                with temp_conn.cursor() as cur:
                    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
                temp_conn.close()
                return pymysql.connect(
                    host=host, port=port, user=user, password=password, database=database,
                    charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor,
                    connect_timeout=2, read_timeout=5, autocommit=True
                )
            except Exception:
                pass
        global _mysql_failed_logged
        if not _mysql_failed_logged:
            logger.info("MySQL connection unavailable (%s); using SQLite fallback: %s", exc, DB_PATH)
            _mysql_failed_logged = True
        return None


def get_sqlite_conn() -> sqlite3.Connection:
    """Fallback connection to local SQLite database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _clean_val(val: Any) -> Any:
    if isinstance(val, Decimal):
        return float(val)
    return val


def _clean_row(row: dict) -> dict:
    return {k: _clean_val(v) for k, v in row.items()}


def query_db(sql: str, params: tuple | list = ()) -> Tuple[List[dict], str]:
    mysql_conn = get_mysql_conn()
    if mysql_conn is not None:
        try:
            with mysql_conn.cursor() as cur:
                mysql_sql = sql.replace("?", "%s")
                cur.execute(mysql_sql, params)
                rows = cur.fetchall()
                return [_clean_row(dict(r)) for r in rows], "mysql"
        except Exception as exc:
            logger.warning("MySQL query failed: %s; falling back to SQLite", exc)
        finally:
            try:
                mysql_conn.close()
            except Exception:
                pass

    conn = get_sqlite_conn()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [_clean_row(dict(r)) for r in rows], "sqlite"
    finally:
        conn.close()


def query_one(sql: str, params: tuple | list = ()) -> Tuple[Optional[dict], str]:
    rows, engine = query_db(sql, params)
    return rows[0] if rows else None, engine


def budget_to_tier(budget: float) -> str:
    for (lo, hi), tier in BUDGET_TIER_MAP.items():
        if lo <= budget < hi:
            return tier
    return "Micro"


def search_influencers(
    category: str | None = None,
    min_er: float = 0.0,
    min_followers: int = 0,
    max_followers: int = 999_999_999,
    goal: str = "awareness",
    budget: float = 5000,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "fit_score",
    exclude_brands: bool = True,
    exclude_suspect_er: bool = True,
) -> list[dict[str, Any]]:
    """Query influencers table, compute fit_score against each influencer's benchmark, sort and paginate in Python."""
    conn = get_sqlite_conn()
    
    conditions = ["engagement_rate >= ?", "followers_count >= ?", "followers_count <= ?"]
    params: list[Any] = [min_er, min_followers, max_followers]

    if exclude_brands:
        conditions.append("(is_brand = 0 OR is_brand IS NULL)")

    if exclude_suspect_er:
        conditions.append("(er_suspect = 0 OR er_suspect IS NULL)")

    if category and category != "All":
        conditions.append("category = ?")
        params.append(category)

    where = "WHERE " + " AND ".join(conditions)
    sql = f"SELECT * FROM influencers {where}"
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    results = []
    budget_tier = budget_to_tier(budget)

    for r in rows:
        d = dict(r)
        d["fit_score"] = compute_fit_score(
            d,
            category=d.get("category") or "Lifestyle",
            budget=budget,
            goal=goal,
            budget_tier=budget_tier,
        )
        d["reliable"] = True
        d["warnings"] = []
        results.append(d)

    # Sort
    sort_key_map = {
        "fit_score":       lambda x: x["fit_score"],
        "roi":             lambda x: (x.get("roi") or 0.0),
        "followers":       lambda x: (x.get("followers_count") or 0),
        "engagement_rate": lambda x: (x.get("engagement_rate") or 0.0),
    }
    key_fn = sort_key_map.get(sort_by, sort_key_map["fit_score"])
    results.sort(key=key_fn, reverse=True)

    return results[offset:offset + limit]


def compute_fit_score(
    inf: dict,
    category: str,
    budget: float,
    goal: str,
    budget_tier: str,
) -> float:
    """Compute fit score (0-100) using the influencer's category benchmark."""
    # When category is None, 'All', or not in benchmarks, use influencer's own category
    effective_cat = category if (category and category != "All" and category in CATEGORY_ER_BENCHMARKS) else (inf.get("category") or "Lifestyle")
    benchmark = float(CATEGORY_ER_BENCHMARKS.get(effective_cat, 0.045))
    er = float(inf.get("engagement_rate", 0) or 0.0)
    er_score = min(er / (benchmark * 2.0), 1.0) * 100.0

    inf_tier = inf.get("follower_tier", "Micro")
    tier_order = ["Nano", "Micro", "Macro", "Mega"]
    budget_tier_idx = tier_order.index(budget_tier) if budget_tier in tier_order else 1
    inf_tier_idx    = tier_order.index(inf_tier)    if inf_tier    in tier_order else 1
    tier_diff = abs(budget_tier_idx - inf_tier_idx)
    tier_score = float([100, 70, 40, 10][min(tier_diff, 3)])

    roi = float(inf.get("roi") if inf.get("roi") is not None else 1.0)
    roi_score = min(max(roi / 3.0, 0.0), 1.0) * 100.0

    if goal == "awareness":
        followers = float(inf.get("followers_count", 0) or 0.0)
        goal_bonus = min(followers / 100_000.0, 1.0) * 100.0
    elif goal == "engagement":
        goal_bonus = er_score
    else:
        goal_bonus = roi_score

    raw = (er_score * 0.35) + (tier_score * 0.25) + (roi_score * 0.25) + (goal_bonus * 0.15)
    return round(min(float(raw), 100.0), 1)


def get_influencer_by_id(iid: int) -> dict | None:
    conn = get_sqlite_conn()
    try:
        row = conn.execute("SELECT * FROM influencers WHERE id = ?", (iid,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_influencer_by_username(username: str) -> dict | None:
    conn = get_sqlite_conn()
    try:
        row = conn.execute("SELECT * FROM influencers WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_dataset_stats() -> dict:
    conn = get_sqlite_conn()
    try:
        total_row = conn.execute("SELECT COUNT(*) AS total FROM influencers WHERE (is_brand = 0 OR is_brand IS NULL) AND (er_suspect = 0 OR er_suspect IS NULL)").fetchone()
        total = total_row["total"] if total_row else 0

        avg_er_row = conn.execute("SELECT AVG(engagement_rate) AS avg_er FROM influencers WHERE (is_brand = 0 OR is_brand IS NULL) AND (er_suspect = 0 OR er_suspect IS NULL)").fetchone()
        avg_er = avg_er_row["avg_er"] if avg_er_row and avg_er_row["avg_er"] is not None else 0.0

        avg_roi_row = conn.execute("SELECT AVG(roi) AS avg_roi FROM influencers WHERE (is_brand = 0 OR is_brand IS NULL) AND (er_suspect = 0 OR er_suspect IS NULL)").fetchone()
        avg_roi = avg_roi_row["avg_roi"] if avg_roi_row and avg_roi_row["avg_roi"] is not None else 0.0

        cat_rows = conn.execute("SELECT DISTINCT category FROM influencers WHERE (is_brand = 0 OR is_brand IS NULL) AND (er_suspect = 0 OR er_suspect IS NULL) ORDER BY category").fetchall()
        categories = [r["category"] for r in cat_rows if r["category"]]

        cat_dist_rows = conn.execute("SELECT category, COUNT(*) AS cnt FROM influencers WHERE (is_brand = 0 OR is_brand IS NULL) AND (er_suspect = 0 OR er_suspect IS NULL) GROUP BY category ORDER BY cnt DESC").fetchall()
        cat_dist = {r["category"]: r["cnt"] for r in cat_dist_rows if r["category"]}
    except Exception as e:
        logger.warning("Error fetching dataset stats: %s", e)
        total = 0
        avg_er = 0.0
        avg_roi = 0.0
        categories = []
        cat_dist = {}
    finally:
        conn.close()

    return {
        "total": total,
        "avg_roi": round(avg_roi, 4),
        "avg_engagement_rate": round(avg_er or 0, 4),
        "categories": categories,
        "category_distribution": cat_dist,
        "db_engine": "sqlite",
        "db_host": "local",
    }


def execute_write(sql: str, params: tuple | list = ()) -> Tuple[bool, str]:
    primary_engine = "sqlite"
    mysql_conn = get_mysql_conn()
    if mysql_conn is not None:
        try:
            with mysql_conn.cursor() as cur:
                mysql_sql = sql.replace("?", "%s")
                cur.execute(mysql_sql, params)
            mysql_conn.commit()
            primary_engine = "mysql"
        except Exception as exc:
            logger.warning("MySQL write error: %s", exc)
        finally:
            try:
                mysql_conn.close()
            except Exception:
                pass

    s_conn = get_sqlite_conn()
    try:
        s_conn.execute(sql, params)
        s_conn.commit()
    except Exception as exc:
        logger.warning("SQLite write error: %s", exc)
    finally:
        s_conn.close()

    return True, primary_engine


def init_users_table():
    s_conn = get_sqlite_conn()
    try:
        s_conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          username TEXT NOT NULL UNIQUE,
          email TEXT NOT NULL UNIQUE,
          password_hash TEXT,
          avatar_url TEXT,
          provider TEXT NOT NULL DEFAULT 'email',
          role TEXT NOT NULL DEFAULT 'Campaign Manager',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        s_conn.commit()
    except Exception as e:
        logger.warning("Error initializing SQLite users table: %s", e)
    finally:
        s_conn.close()

    m_conn = get_mysql_conn()
    if m_conn is not None:
        try:
            with m_conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                  id INT AUTO_INCREMENT PRIMARY KEY,
                  username VARCHAR(100) NOT NULL UNIQUE,
                  email VARCHAR(150) NOT NULL UNIQUE,
                  password_hash VARCHAR(255),
                  avatar_url VARCHAR(500),
                  provider VARCHAR(50) DEFAULT 'email',
                  role VARCHAR(100) DEFAULT 'Campaign Manager',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                );
                """)
            m_conn.commit()
        except Exception as e:
            logger.warning("Error initializing MySQL users table: %s", e)
        finally:
            try:
                m_conn.close()
            except Exception:
                pass

init_users_table()


def create_user(
    username: str,
    email: str,
    password_hash: str | None = None,
    avatar_url: str | None = None,
    provider: str = "email",
    role: str = "Campaign Manager",
) -> dict:
    existing = get_user_by_email(email)
    if existing:
        return existing

    sql = """
    INSERT INTO users (username, email, password_hash, avatar_url, provider, role)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    execute_write(sql, (username, email, password_hash, avatar_url, provider, role))
    user = get_user_by_email(email)
    return user or {
        "username": username,
        "email": email,
        "avatar_url": avatar_url,
        "provider": provider,
        "role": role,
    }


def get_user_by_email(email: str) -> dict | None:
    row, _ = query_one("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email,))
    return row


def get_user_by_username(username: str) -> dict | None:
    row, _ = query_one("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username,))
    return row


def get_all_users() -> list[dict]:
    rows, _ = query_db("SELECT id, username, email, avatar_url, provider, role, created_at FROM users ORDER BY id DESC")
    return rows


def update_user_password(email: str, new_password_hash: str) -> bool:
    sql = "UPDATE users SET password_hash = ? WHERE LOWER(email) = LOWER(?)"
    execute_write(sql, (new_password_hash, email))
    return True


def update_user_profile(email: str, username: str, role: str | None = None, avatar_url: str | None = None) -> dict | None:
    fields = ["username = ?"]
    params = [username]
    if role:
        fields.append("role = ?")
        params.append(role)
    if avatar_url:
        fields.append("avatar_url = ?")
        params.append(avatar_url)
    params.append(email)
    sql = f"UPDATE users SET {', '.join(fields)} WHERE LOWER(email) = LOWER(?)"
    execute_write(sql, params)
    return get_user_by_email(email)


def ensure_influencers_db() -> int:
    """Ensure data/influencers.db exists and has records; rebuilds from data/influencers_clean.csv if missing or empty.
    
    Returns the count of influencers in the database.
    """
    import csv

    csv_path = PROJECT_ROOT / "data" / "influencers_clean.csv"
    needs_rebuild = False

    if not DB_PATH.exists():
        needs_rebuild = True
    else:
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='influencers'")
            if cur.fetchone()[0] == 0:
                needs_rebuild = True
            else:
                cur.execute("SELECT count(*) FROM influencers")
                c = cur.fetchone()[0]
                if c == 0:
                    needs_rebuild = True
                else:
                    conn.close()
                    return c
            conn.close()
        except Exception:
            needs_rebuild = True

    if not needs_rebuild:
        return 0

    if not csv_path.exists():
        logger.error(f"Cannot rebuild influencers.db: {csv_path} does not exist!")
        return 0

    logger.info(f"Rebuilding {DB_PATH.name} automatically from {csv_path.name}...")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    try:
        with conn:
            conn.execute("DROP TABLE IF EXISTS influencers")
            conn.execute("""
                CREATE TABLE influencers (
                    id                  INTEGER PRIMARY KEY,
                    username            TEXT NOT NULL,
                    full_name           TEXT,
                    category            TEXT,
                    sub_category        TEXT,
                    biography           TEXT,
                    followers_count     INTEGER,
                    following_count     INTEGER,
                    media_count         INTEGER,
                    avg_likes           REAL,
                    avg_comments        REAL,
                    avg_video_views     INTEGER DEFAULT 0,
                    engagement_rate     REAL,
                    posting_frequency   REAL,
                    estimated_reach     INTEGER,
                    is_verified         INTEGER DEFAULT 0,
                    country             TEXT DEFAULT 'IN',
                    follower_tier       TEXT,
                    audience_female_pct REAL,
                    audience_male_pct   REAL,
                    audience_age_18_24  REAL,
                    audience_age_25_34  REAL,
                    audience_age_35_44  REAL,
                    posts_used          INTEGER DEFAULT 0,
                    spend               REAL,
                    revenue             REAL,
                    roi                 REAL,
                    roi_source          TEXT DEFAULT 'model_estimate',
                    is_brand            INTEGER DEFAULT 0,
                    er_suspect          INTEGER DEFAULT 0,
                    profile_url         TEXT,
                    profile_screenshot  TEXT,
                    collected_at        TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_inf_category ON influencers(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_inf_tier ON influencers(follower_tier)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_inf_username ON influencers(username)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_inf_is_brand ON influencers(is_brand)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_inf_er_suspect ON influencers(er_suspect)")

            records = []
            with open(csv_path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Clean/cast types
                    cleaned_row = {}
                    for k, v in row.items():
                        if k in ("id", "followers_count", "following_count", "media_count",
                                 "avg_video_views", "estimated_reach", "is_verified",
                                 "posts_used", "is_brand", "er_suspect"):
                            cleaned_row[k] = int(v) if v is not None and str(v).strip() != "" else 0
                        elif k in ("avg_likes", "avg_comments", "engagement_rate",
                                   "posting_frequency", "audience_female_pct", "audience_male_pct",
                                   "audience_age_18_24", "audience_age_25_34", "audience_age_35_44",
                                   "spend", "revenue", "roi"):
                            cleaned_row[k] = float(v) if v is not None and str(v).strip() != "" else 0.0
                        else:
                            cleaned_row[k] = v if v is not None else ""
                    records.append(cleaned_row)

            if records:
                cols = list(records[0].keys())
                placeholders = ":" + ", :".join(cols)
                sql = f"INSERT INTO influencers ({', '.join(cols)}) VALUES ({placeholders})"
                conn.executemany(sql, records)

            # Ensure users table is also present in SQLite
            conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              email TEXT NOT NULL UNIQUE,
              password_hash TEXT,
              avatar_url TEXT,
              provider TEXT NOT NULL DEFAULT 'email',
              role TEXT NOT NULL DEFAULT 'Campaign Manager',
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

        count = len(records)
        logger.info(f"✅ Successfully rebuilt {DB_PATH.name} with {count} influencers from CSV")
        return count
    finally:
        conn.close()

