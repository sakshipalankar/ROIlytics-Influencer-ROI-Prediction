"""Analytics router: dataset overview and creator profiles."""
from fastapi import APIRouter, HTTPException
from ..schemas.schemas import AnalyticsOverview
from ..services.predictor import PredictorService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
async def get_overview() -> AnalyticsOverview:
    """Return dataset summary and creator profiles for presets."""
    try:
        svc = PredictorService.get()
        data = svc.get_overview()
        return AnalyticsOverview(**data)
    except Exception as exc:
        logger.exception("Overview failed")
        raise HTTPException(status_code=500, detail=str(exc))
