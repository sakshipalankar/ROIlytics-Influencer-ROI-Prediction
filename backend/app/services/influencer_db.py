"""Influencer database service — queries SQLite influencer dataset."""
from __future__ import annotations

import sqlite3
import os
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "data" / "influencers.db"

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

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


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
    conn = get_conn()
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
    # Fetch more rows so we can score and sort them
    sql = f"SELECT * FROM influencers {where} LIMIT 500 OFFSET {offset}"
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    # Score each influencer
    budget_tier = budget_to_tier(budget)
    results = []
    for row in rows:
        d = dict(row)
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
      - Follower tier fit 20%  (budget ↔ follower tier alignment)
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
        # Followers matter more → boost Macro/Mega
        goal_bonus = (inf.get("followers_count", 0) / 1_000_000) * 10
    elif goal == "engagement":
        # Pure ER focus
        goal_bonus = er_score * 0.1
    else:  # sales / conversion
        goal_bonus = roi_score * 0.1

    raw = (er_score * 0.35) + (tier_score * 0.20) + (roi_score * 0.30) + (goal_bonus * 0.15)
    return round(min(raw, 100), 1)


def get_influencer_by_username(username: str) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM influencers WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_influencer_by_id(iid: int) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM influencers WHERE id = ?", (iid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_dataset_stats() -> dict:
    conn = get_conn()
    total       = conn.execute("SELECT COUNT(*) FROM influencers").fetchone()[0]
    avg_roi     = conn.execute("SELECT AVG(roi) FROM influencers").fetchone()[0]
    avg_er      = conn.execute("SELECT AVG(engagement_rate) FROM influencers").fetchone()[0]
    verified    = conn.execute("SELECT COUNT(*) FROM influencers WHERE is_verified=1").fetchone()[0]
    categories  = [r[0] for r in conn.execute("SELECT DISTINCT category FROM influencers ORDER BY category").fetchall()]
    countries   = [r[0] for r in conn.execute("SELECT DISTINCT country FROM influencers ORDER BY country").fetchall()]
    cat_dist    = {r[0]: r[1] for r in conn.execute(
        "SELECT category, COUNT(*) as cnt FROM influencers GROUP BY category ORDER BY cnt DESC"
    ).fetchall()}
    tier_dist   = {r[0]: r[1] for r in conn.execute(
        "SELECT follower_tier, COUNT(*) as cnt FROM influencers GROUP BY follower_tier"
    ).fetchall()}
    conn.close()
    return {
        "total": total,
        "avg_roi": round(avg_roi or 0, 3),
        "avg_engagement_rate": round(avg_er or 0, 4),
        "verified_count": verified,
        "categories": categories,
        "countries": countries,
        "category_distribution": cat_dist,
        "tier_distribution": tier_dist,
    }
