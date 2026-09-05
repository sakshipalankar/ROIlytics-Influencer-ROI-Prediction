"""Model results router: benchmark metrics and feature importance."""
from fastapi import APIRouter, HTTPException
from ..schemas.schemas import ModelResultsResponse
from ..services.predictor import PredictorService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("/results", response_model=ModelResultsResponse)
async def get_model_results() -> ModelResultsResponse:
    """Return model benchmark results from training."""
    try:
        svc = PredictorService.get()
        raw = svc.get_model_results()

        # Ensure required structure
        models = raw.get("models", [])
        if not models:
            models = [{"name": raw.get("best_model", "Random Forest"), "r2": 0.0, "mae": 0.0, "rmse": 0.0, "cv_r2": 0.0}]

        return ModelResultsResponse(
            best_model=raw.get("best_model", "Random Forest"),
            models=models,
            feature_importance=raw.get("feature_importance", []),
            training_samples=raw.get("training_samples", 0),
        )
    except Exception as exc:
        logger.exception("Model results failed")
        raise HTTPException(status_code=500, detail=str(exc))
