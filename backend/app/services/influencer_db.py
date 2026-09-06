"""Influencer database service — dual-engine with MySQL (primary) and SQLite (automatic fallback)."""
from __future__ import annotations

import os
import sqlite3
import logging
from pathlib import Path
from typing import Any, Tuple, List, Optional
from dotenv import load_dotenv

try:
    import pymysql
    import pymysql.cursors
    PYMYSQL_AVAILABLE = True
except ImportError:
    PYMYSQL_AVAILABLE = False

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "data" / "influencers.db"
load_dotenv(PROJECT_ROOT / ".env")

# MySQL Settings from environment
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "roilytics_db")

CATEGORY_ER_BENCHMARKS = {
    "Fitness":   0.055,
    "Fashion":   0.045,
    "Tech":      0.038,
    "Food":      0.052,
    "Travel":    0.042,
    "Lifestyle": 0.048,
    "Beauty":    0.056,
    "Gaming":    0.040,
    "Finance":   0.033,
    "Education": 0.036,
}

BUDGET_TIER_MAP = {
    (0,       2_000):    "Nano",
    (2_000,   15_000):   "Micro",
    (15_000,  100_000):  "Macro",
    (100_000, 999_999_999): "Mega",
}

_mysql_failed_logged = False


def get_mysql_conn():
    """Attempt to establish a MySQL connection using PyMySQL."""
    if not PYMYSQL_AVAILABLE:
        return None
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=2,
            read_timeout=5,
            autocommit=True,
        )
        return conn
    except Exception as exc:
        global _mysql_failed_logged
        if not _mysql_failed_logged:
            logger.info("MySQL connection unavailable (%s); using SQLite fallback: %s", exc, DB_PATH)
            _mysql_failed_logged = True
        return None


def get_sqlite_conn() -> sqlite3.Connection:
    """Fallback connection to local SQLite database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def query_db(sql: str, params: tuple | list = ()) -> Tuple[List[dict], str]:
    """
    Execute a read query against MySQL if available, otherwise SQLite.
    sql should use '?' placeholders (converted to '%s' for MySQL).
    Returns (list_of_dict_records, engine_name).
    """
    mysql_conn = get_mysql_conn()
    if mysql_conn is not None:
        try:
            with mysql_conn.cursor() as cur:
                # Convert SQLite ? placeholders to MySQL %s
                mysql_sql = sql.replace("?", "%s")
                cur.execute(mysql_sql, params)
                rows = cur.fetchall()
                return [dict(r) for r in rows], "mysql"
        except Exception as exc:
            logger.warning("MySQL query failed: %s; falling back to SQLite", exc)
        finally:
            try:
                mysql_conn.close()
            except Exception:
                pass

    # SQLite fallback
    conn = get_sqlite_conn()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows], "sqlite"
    finally:
        conn.close()


def query_one(sql: str, params: tuple | list = ()) -> Tuple[Optional[dict], str]:
    """Execute a query returning a single record."""
    rows, engine = query_db(sql, params)
    return rows[0] if rows else None, engine


def budget_to_tier(budget: float) -> str:
    for (lo, hi), tier in BUDGET_TIER_MAP.items():
        if lo <= budget < hi:
            return tier
    return "Micro"


def search_influencers(
    category: str | None = None,
    follower_tier: str | None = None,
    min_er: float = 0.0,
    min_followers: int = 0,
    max_followers: int = 999_999_999,
    country: str | None = None,
    is_verified: bool | None = None,
    goal: str = "awareness",
    budget: float = 5000,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "fit_score",
) -> list[dict[str, Any]]:
    """Query influencers with filters, compute fit_score, return sorted list."""
    conditions = ["engagement_rate >= ?", "followers_count >= ?", "followers_count <= ?"]
    params: list[Any] = [min_er, min_followers, max_followers]

    if category and category != "All":
        conditions.append("category = ?")
        params.append(category)
    if follower_tier and follower_tier != "All":
        conditions.append("follower_tier = ?")
        params.append(follower_tier)
    if country and country != "All":
        conditions.append("country = ?")
        params.append(country)
    if is_verified is True:
        conditions.append("is_verified = 1")

    where = "WHERE " + " AND ".join(conditions)
    # Fetch up to 500 rows so we can score and rank them accurately
    sql = f"SELECT * FROM influencers {where} LIMIT 500 OFFSET {offset}"
    rows, _engine = query_db(sql, params)

    # Score each influencer
    budget_tier = budget_to_tier(budget)
    results = []
    for d in rows:
        d["fit_score"] = compute_fit_score(d, category or "Lifestyle", budget, goal, budget_tier)
        results.append(d)

    # Sort
    sort_key_map = {
        "fit_score":       lambda x: x["fit_score"],
        "roi":             lambda x: x["roi"],
        "followers":       lambda x: x["followers_count"],
        "engagement_rate": lambda x: x["engagement_rate"],
    }
    key_fn = sort_key_map.get(sort_by, sort_key_map["fit_score"])
    results.sort(key=key_fn, reverse=True)

    return results[:limit]


def compute_fit_score(
    inf: dict,
    category: str,
    budget: float,
    goal: str,
    budget_tier: str,
) -> float:
    """
    Fit Score (0–100):
      - Engagement score  35%  (ER vs category benchmark)
      - Follower tier fit 20%  (budget <-> follower tier alignment)
      - ROI score         30%  (scaled predicted ROI)
      - Goal alignment    15%  (ER weight depends on goal)
    """
    # Engagement score
    benchmark = CATEGORY_ER_BENCHMARKS.get(category, 0.045)
    er = inf.get("engagement_rate", 0)
    er_score = min(er / (benchmark * 2), 1.0) * 100  # 0–100

    # Follower tier fit (budget alignment)
    inf_tier = inf.get("follower_tier", "Micro")
    tier_order = ["Nano", "Micro", "Macro", "Mega"]
    budget_tier_idx = tier_order.index(budget_tier) if budget_tier in tier_order else 1
    inf_tier_idx    = tier_order.index(inf_tier)    if inf_tier    in tier_order else 1
    tier_diff = abs(budget_tier_idx - inf_tier_idx)
    tier_score = [100, 70, 40, 10][min(tier_diff, 3)]

    # ROI score (0–100, clamped at ROI=5x)
    roi = inf.get("roi", 1.0)
    roi_score = min(max(roi / 5.0, 0), 1.0) * 100

    # Goal alignment adjustment
    if goal == "awareness":
        # Followers matter more -> boost Macro/Mega
        goal_bonus = (inf.get("followers_count", 0) / 1_000_000) * 10
    elif goal == "engagement":
        # Pure ER focus
        goal_bonus = er_score * 0.1
    else:  # sales / conversion
        goal_bonus = roi_score * 0.1

    raw = (er_score * 0.35) + (tier_score * 0.20) + (roi_score * 0.30) + (goal_bonus * 0.15)
    return round(min(raw, 100), 1)


def get_influencer_by_username(username: str) -> dict | None:
    row, _ = query_one("SELECT * FROM influencers WHERE username = ?", (username,))
    return row


def get_influencer_by_id(iid: int) -> dict | None:
    row, _ = query_one("SELECT * FROM influencers WHERE id = ?", (iid,))
    return row


def get_dataset_stats() -> dict:
    total_row, engine = query_one("SELECT COUNT(*) AS total FROM influencers")
    total = total_row["total"] if total_row else 0

    avg_roi_row, _ = query_one("SELECT AVG(roi) AS avg_roi FROM influencers")
    avg_roi = avg_roi_row["avg_roi"] if avg_roi_row and avg_roi_row["avg_roi"] is not None else 0.0

    avg_er_row, _ = query_one("SELECT AVG(engagement_rate) AS avg_er FROM influencers")
    avg_er = avg_er_row["avg_er"] if avg_er_row and avg_er_row["avg_er"] is not None else 0.0

    verified_row, _ = query_one("SELECT COUNT(*) AS verified FROM influencers WHERE is_verified=1")
    verified = verified_row["verified"] if verified_row else 0

    cat_rows, _ = query_db("SELECT DISTINCT category FROM influencers ORDER BY category")
    categories = [r["category"] for r in cat_rows if r.get("category")]

    country_rows, _ = query_db("SELECT DISTINCT country FROM influencers ORDER BY country")
    countries = [r["country"] for r in country_rows if r.get("country")]

    cat_dist_rows, _ = query_db("SELECT category, COUNT(*) AS cnt FROM influencers GROUP BY category ORDER BY cnt DESC")
    cat_dist = {r["category"]: r["cnt"] for r in cat_dist_rows if r.get("category")}

    tier_dist_rows, _ = query_db("SELECT follower_tier, COUNT(*) AS cnt FROM influencers GROUP BY follower_tier")
    tier_dist = {r["follower_tier"]: r["cnt"] for r in tier_dist_rows if r.get("follower_tier")}

    return {
        "total": total,
        "avg_roi": round(avg_roi or 0, 3),
        "avg_engagement_rate": round(avg_er or 0, 4),
        "verified_count": verified,
        "categories": categories,
        "countries": countries,
        "category_distribution": cat_dist,
        "tier_distribution": tier_dist,
        "db_engine": engine,
        "db_host": MYSQL_HOST if engine == "mysql" else "local",
    }
