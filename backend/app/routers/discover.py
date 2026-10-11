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


def _get_note_for_row(row: dict) -> str | None:
    source = str(row.get("source", "official"))
    if source == "official":
        return None
    elif source == "public_snapshot":
        dt = row.get("collected_at") or row.get("fetched_at") or ""
        dt_str = "Unknown Date"
        try:
            from datetime import datetime
            if dt:
                dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                dt_str = dt_obj.strftime("%d %b %Y")
        except Exception:
            pass
        base_note = f"Manual snapshot, collected from public profile on {dt_str}"
        c_note = row.get("collected_note")
        if c_note and str(c_note).strip() and str(c_note).strip() != "None":
            return f"{base_note} | {str(c_note).strip()}"
        return base_note
    return "Third-party public data, may be incomplete"


def row_to_card(row: dict, idx: int) -> InfluencerCard:
    avatar_seed = int(row.get("id") or (idx + 1))
    return InfluencerCard(
        id=row.get("id"),
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
        audience_female_pct=float(row.get("audience_female_pct")) if row.get("audience_female_pct") is not None else None,
        audience_male_pct=float(row.get("audience_male_pct")) if row.get("audience_male_pct") is not None else None,
        fit_score=float(row.get("fit_score") or 50.0),
        roi=float(row.get("roi")) if row.get("roi") is not None else None,
        spend=float(row.get("spend") or 0.0),
        revenue=float(row.get("revenue")) if row.get("revenue") is not None else None,
        profile_pic_url=pic_url(row["username"], row.get("full_name") or row["username"], avatar_seed),
        profile_url=str(row.get("profile_url") or f"https://www.instagram.com/{row['username']}/"),
        profile_screenshot=row.get("profile_screenshot"),
        roi_source=str(row.get("roi_source") or "model_estimate"),
        is_brand=int(row.get("is_brand") or 0),
        er_suspect=int(row.get("er_suspect") or 0),
        source=str(row.get("source", "official")),
        reliable=bool(row.get("reliable", True)),
        warnings=row.get("warnings", []),
        fetched_at=str(row.get("fetched_at", "")),
        collected_at=str(row.get("collected_at", "")),
        collected_note=str(row.get("collected_note", "")),
        note=_get_note_for_row(row)
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
            min_er=body.min_er,
            min_followers=body.min_followers,
            max_followers=body.max_followers,
            goal=body.goal,
            budget=body.budget,
            limit=body.limit,
            offset=body.offset,
            sort_by=body.sort_by,
        )
        reliable_rows = [r for r in rows if r.get("reliable", True)]
        unreliable_rows = [r for r in rows if not r.get("reliable", True)]
        
        reliable_cards = [row_to_card(r, i) for i, r in enumerate(reliable_rows)]
        unreliable_cards = [row_to_card(r, i) for i, r in enumerate(unreliable_rows)]
        
        notice = None
        if len(reliable_cards) < 3:
            notice = "Add more profiles in this category for a meaningful ranking."
            
        return DiscoverResponse(
            influencers=reliable_cards,
            unreliable_influencers=unreliable_cards,
            total_found=len(reliable_cards) + len(unreliable_cards),
            category=body.category,
            budget_tier=budget_to_tier(body.budget),
            notice=notice,
        )
    except Exception as exc:
        logger.exception("Discovery failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/top")
async def get_top_influencers(
    category: Optional[str] = Query(None, description="Category filter or empty for all"),
    budget: float = Query(5000.0, description="Campaign budget"),
    goal: str = Query("awareness", description="Campaign goal"),
    limit: int = Query(10, ge=1, le=100, description="Max top influencers to return")
):
    """
    Get top N influencers ranked by fit_score.
    Reuses search_influencers logic.
    """
    try:
        cat = category if category and category != "All" else None
        rows = search_influencers(
            category=cat,
            budget=budget,
            goal=goal,
            limit=limit,
            offset=0,
            sort_by="fit_score"
        )
        cards = [row_to_card(r, i) for i, r in enumerate(rows)]
        return {
            "top_influencers": cards,
            "category": category or "All",
            "budget": budget,
            "goal": goal,
            "count": len(cards)
        }
    except Exception as exc:
        logger.exception("Failed to fetch top influencers")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/reload")
async def reload_dataset():
    """
    Re-run scraped data ingestion without restarting the server.
    """
    try:
        import subprocess
        import sys
        from pathlib import Path
        project_root = Path(__file__).resolve().parents[3]
        cmd = [sys.executable, "-m", "backend.scripts.ingest_scraped"]
        result = subprocess.run(cmd, cwd=str(project_root), capture_output=True, text=True, check=True)
        stats = get_dataset_stats()
        return {
            "status": "success",
            "message": "Dataset re-ingested successfully",
            "output": result.stdout[-500:],
            "stats": stats
        }
    except Exception as exc:
        logger.exception("Failed to reload dataset")
        raise HTTPException(status_code=500, detail=f"Reload failed: {exc}")


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
    if "profile_url" not in row or not row["profile_url"]:
        row["profile_url"] = f"https://www.instagram.com/{row['username']}/"
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
            if "profile_url" not in row or not row["profile_url"]:
                row["profile_url"] = f"https://www.instagram.com/{row['username']}/"
            row["fit_score"] = compute_fit_score(
                row, row["category"], body.budget, body.goal, budget_to_tier(body.budget)
            )
            results.append(row)
    if not results:
        raise HTTPException(status_code=404, detail="No influencers found")
    return {"influencers": results, "budget": body.budget, "goal": body.goal}
