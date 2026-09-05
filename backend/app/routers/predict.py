"""Prediction router: single predict, batch CSV, and ROI simulation."""
from __future__ import annotations

import io
import csv
import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..schemas.schemas import PredictRequest, PredictResponse, SimulateResponse, SimulatePoint
from ..services.predictor import PredictorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/predict", tags=["predict"])

CATEGORIES = ["Fitness", "Fashion", "Tech", "Food", "Travel", "Lifestyle"]


@router.post("", response_model=PredictResponse)
async def predict_single(body: PredictRequest) -> PredictResponse:
    """Predict ROI for a single influencer."""
    try:
        svc = PredictorService.get()
        result = svc.predict(
            followers_count=body.followers_count,
            media_count=body.media_count,
            avg_likes=body.avg_likes,
            avg_comments=body.avg_comments,
            category=body.category,
            posting_frequency=body.posting_frequency,
            spend=body.spend,
        )
        return PredictResponse(**result)
    except Exception as exc:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/simulate", response_model=SimulateResponse)
async def simulate_budget(
    followers_count: int = Query(..., ge=1000),
    media_count: int = Query(..., ge=1),
    avg_likes: float = Query(..., ge=0),
    avg_comments: float = Query(..., ge=0),
    category: str = Query("Lifestyle"),
    posting_frequency: float = Query(3.5, ge=0, le=30),
    spend_min: float = Query(500, ge=100),
    spend_max: float = Query(50000, le=10_000_000),
    steps: int = Query(20, ge=5, le=100),
) -> SimulateResponse:
    """Simulate ROI across a spend range to plot a budget curve."""
    try:
        svc = PredictorService.get()
        points_raw = svc.simulate(
            followers_count=followers_count,
            media_count=media_count,
            avg_likes=avg_likes,
            avg_comments=avg_comments,
            category=category,
            posting_frequency=posting_frequency,
            spend_min=spend_min,
            spend_max=spend_max,
            steps=steps,
        )
        points = [SimulatePoint(**p) for p in points_raw]
        return SimulateResponse(points=points)
    except Exception as exc:
        logger.exception("Simulation failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/batch")
async def predict_batch(file: UploadFile = File(...)) -> StreamingResponse:
    """
    Accept a CSV file with influencer data, return enriched CSV with predictions.
    Required columns: followers_count, media_count, avg_likes, avg_comments,
                      category, posting_frequency, spend
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    try:
        contents = await file.read()
        reader = csv.DictReader(io.StringIO(contents.decode("utf-8")))
        rows = list(reader)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {exc}")

    required = {"followers_count", "media_count", "avg_likes", "avg_comments",
                "category", "posting_frequency", "spend"}
    if rows and not required.issubset(set(rows[0].keys())):
        missing = required - set(rows[0].keys())
        raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

    svc = PredictorService.get()
    results = []
    for row in rows:
        try:
            pred = svc.predict(
                followers_count=int(float(row["followers_count"])),
                media_count=int(float(row["media_count"])),
                avg_likes=float(row["avg_likes"]),
                avg_comments=float(row["avg_comments"]),
                category=str(row["category"]).strip() or "Lifestyle",
                posting_frequency=float(row["posting_frequency"]),
                spend=float(row["spend"]),
            )
            results.append({**row, **pred})
        except Exception as exc:
            results.append({**row, "error": str(exc)})

    output = io.StringIO()
    if results:
        writer = csv.DictWriter(output, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    output.seek(0)
    return StreamingResponse(
        iter([output.read()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=roi_predictions.csv"},
    )
