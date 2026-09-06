"""Influencer discovery router."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from ..schemas.schemas import (
    BrandProfileRequest, DiscoverResponse, InfluencerCard,
    DatasetStats, ShortlistCompareRequest
)
from ..services.influencer_db import (
    search_influencers, get_influencer_by_id, get_influencer_by_username,
    get_dataset_stats, budget_to_tier, compute_fit_score
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/discover", tags=["discover"])

AVATAR_BASE = "https://ui-avatars.com/api/?size=128&bold=true&background="
AVATAR_COLORS = ["6366f1", "8b5cf6", "10b981", "f59e0b", "f43f5e", "38bdf8",
                 "ec4899", "14b8a6", "f97316", "84cc16"]


def pic_url(username: str, full_name: str, idx: int) -> str:
    color = AVATAR_COLORS[idx % len(AVATAR_COLORS)]
    initials = "".join(p[0].upper() for p in full_name.split()[:2])
    return f"{AVATAR_BASE}{color}&color=fff&name={initials}"


def row_to_card(row: dict, idx: int) -> InfluencerCard:
    return InfluencerCard(
        id=int(row["id"]),
        username=str(row["username"]),
        full_name=str(row.get("full_name") or row["username"]),
        category=str(row["category"]),
        sub_category=str(row.get("sub_category") or ""),
        biography=str(row.get("biography") or ""),
        followers_count=int(row.get("followers_count") or 0),
        avg_likes=float(row.get("avg_likes") or 0.0),
        avg_comments=float(row.get("avg_comments") or 0.0),
        engagement_rate=float(row.get("engagement_rate") or 0.0),
        posting_frequency=float(row.get("posting_frequency") or 1.0),
        estimated_reach=int(row.get("estimated_reach") or 0),
        is_verified=bool(row.get("is_verified", False)),
        country=str(row.get("country") or "IN"),
        follower_tier=str(row.get("follower_tier") or "Micro"),
        audience_female_pct=float(row.get("audience_female_pct") or 0.5),
        audience_male_pct=float(row.get("audience_male_pct") or 0.5),
        fit_score=float(row.get("fit_score") or 50.0),
        roi=float(row.get("roi") or 1.0),
        spend=float(row.get("spend") or 0.0),
        revenue=float(row.get("revenue") or 0.0),
        profile_pic_url=pic_url(row["username"], row.get("full_name") or row["username"], int(row["id"])),
    )


@router.post("", response_model=DiscoverResponse)
async def discover_influencers(body: BrandProfileRequest) -> DiscoverResponse:
    """
    Main discovery endpoint.
    Company sends brand profile → returns ranked influencer list.
    """
    try:
        rows = search_influencers(
            category=body.category if body.category != "All" else None,
            follower_tier=body.follower_tier if body.follower_tier not in (None, "All") else None,
            min_er=body.min_er,
            min_followers=body.min_followers,
            max_followers=body.max_followers,
            country=body.country if body.country not in (None, "All") else None,
            is_verified=body.is_verified,
            goal=body.goal,
            budget=body.budget,
            limit=body.limit,
            offset=body.offset,
            sort_by=body.sort_by,
        )
        cards = [row_to_card(r, i) for i, r in enumerate(rows)]
        return DiscoverResponse(
            influencers=cards,
            total_found=len(cards),
            category=body.category,
            budget_tier=budget_to_tier(body.budget),
        )
    except Exception as exc:
        logger.exception("Discovery failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/stats", response_model=DatasetStats)
async def dataset_stats() -> DatasetStats:
    """Return overall dataset statistics."""
    try:
        s = get_dataset_stats()
        return DatasetStats(**s)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/influencer/{iid}")
async def get_influencer(iid: int):
    """Get full influencer profile by ID."""
    row = get_influencer_by_id(iid)
    if not row:
        raise HTTPException(status_code=404, detail="Influencer not found")
    idx = row["id"] % 10
    row["profile_pic_url"] = pic_url(row["username"], row["full_name"], idx)
    row["is_verified"] = bool(row["is_verified"])
    return row


@router.post("/compare")
async def compare_influencers(body: ShortlistCompareRequest):
    """Compare multiple influencers side by side."""
    results = []
    for iid in body.influencer_ids:
        row = get_influencer_by_id(iid)
        if row:
            row["is_verified"] = bool(row["is_verified"])
            row["profile_pic_url"] = pic_url(row["username"], row["full_name"], row["id"])
            row["fit_score"] = compute_fit_score(
                row, row["category"], body.budget, body.goal, budget_to_tier(body.budget)
            )
            results.append(row)
    if not results:
        raise HTTPException(status_code=404, detail="No influencers found")
    return {"influencers": results, "budget": body.budget, "goal": body.goal}
