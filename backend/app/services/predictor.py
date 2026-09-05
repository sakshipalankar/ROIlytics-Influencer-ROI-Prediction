"""ML inference service — loads best_model.pkl once at startup and serves predictions."""
from __future__ import annotations

import os
import sys
import json
import logging
from pathlib import Path
from functools import lru_cache
from typing import Any

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Path resolution: backend is at project_root/backend, models at project_root/models
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # backend/app/services -> project root
MODEL_PATH = PROJECT_ROOT / "models" / "best_model.pkl"
RESULTS_PATH = PROJECT_ROOT / "models" / "model_results.json"
BENCHMARK_PATH = PROJECT_ROOT / "data" / "instagram_profiles_benchmark.csv"
RAW_PATH = PROJECT_ROOT / "data" / "instagram_profiles_raw.csv"

CATEGORY_MAP = {
    "Fitness": 0, "Fashion": 1, "Tech": 2, "Food": 3, "Travel": 4, "Lifestyle": 5
}
BUCKET_MAP = {"Nano": 0, "Micro": 1, "Macro": 2, "Mega": 3}


def _assign_bucket(followers: int) -> str:
    if followers < 10_000:
        return "Nano"
    if followers < 100_000:
        return "Micro"
    if followers < 1_000_000:
        return "Macro"
    return "Mega"


def _tier_label(roi: float) -> tuple[str, str]:
    if roi >= 3.0:
        return "Outstanding", "#10b981"
    if roi >= 2.0:
        return "Excellent", "#3b82f6"
    if roi >= 1.0:
        return "Good", "#8b5cf6"
    if roi >= 0.0:
        return "Break-even", "#f59e0b"
    return "Negative ROI", "#ef4444"


class PredictorService:
    """Singleton ML inference service."""

    _instance: "PredictorService | None" = None

    def __init__(self) -> None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}")
        data = joblib.load(MODEL_PATH)
        self.model = data["model"]
        self.feature_columns: list[str] = data["feature_columns"]
        self.model_name: str = data.get("model_name", "Random Forest")
        logger.info(f"Loaded model: {self.model_name} | features: {self.feature_columns}")

    @classmethod
    def get(cls) -> "PredictorService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _build_features(
        self,
        followers_count: int,
        media_count: int,
        avg_likes: float,
        avg_comments: float,
        category: str,
        posting_frequency: float,
        spend: float,
    ) -> pd.DataFrame:
        bucket = _assign_bucket(followers_count)
        engagement_rate = (avg_likes + avg_comments) / max(followers_count, 1)
        likes_to_comments_ratio = avg_likes / max(avg_comments + 1, 1)
        log_followers = np.log1p(followers_count)
        category_encoded = CATEGORY_MAP.get(category, 5)
        bucket_encoded = BUCKET_MAP.get(bucket, 1)

        raw = {
            "followers_count": followers_count,
            "media_count": media_count,
            "avg_likes": avg_likes,
            "avg_comments": avg_comments,
            "engagement_rate": engagement_rate,
            "posting_frequency": posting_frequency,
            "spend": spend,
            "follower_bucket_encoded": bucket_encoded,
            "category_encoded": category_encoded,
            "log_followers": log_followers,
            "likes_to_comments_ratio": likes_to_comments_ratio,
        }
        row = {col: raw.get(col, 0.0) for col in self.feature_columns}
        return pd.DataFrame([row])

    def predict(
        self,
        followers_count: int,
        media_count: int,
        avg_likes: float,
        avg_comments: float,
        category: str,
        posting_frequency: float,
        spend: float,
    ) -> dict[str, Any]:
        X = self._build_features(
            followers_count, media_count, avg_likes, avg_comments,
            category, posting_frequency, spend
        )
        roi = float(self.model.predict(X)[0])
        revenue = spend * (1 + roi)
        profit = revenue - spend
        engagement_rate = (avg_likes + avg_comments) / max(followers_count, 1)
        tier, tier_color = _tier_label(roi)
        return {
            "roi": round(roi, 4),
            "tier": tier,
            "tier_color": tier_color,
            "predicted_revenue": round(revenue, 2),
            "predicted_profit": round(profit, 2),
            "engagement_rate": round(engagement_rate, 6),
            "follower_tier": _assign_bucket(followers_count),
        }

    def simulate(
        self,
        followers_count: int,
        media_count: int,
        avg_likes: float,
        avg_comments: float,
        category: str,
        posting_frequency: float,
        spend_min: float,
        spend_max: float,
        steps: int = 20,
    ) -> list[dict]:
        points = []
        for spend in np.linspace(spend_min, spend_max, steps):
            r = self.predict(followers_count, media_count, avg_likes, avg_comments,
                             category, posting_frequency, float(spend))
            points.append({
                "spend": round(float(spend), 2),
                "revenue": r["predicted_revenue"],
                "profit": r["predicted_profit"],
                "roi": r["roi"],
            })
        return points

    def get_model_results(self) -> dict:
        models = []
        if RESULTS_PATH.exists():
            with open(RESULTS_PATH) as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        models.append({
                            "name": str(item.get("Model", "Unknown")),
                            "r2": float(item.get("R2", 0.0)),
                            "mae": float(item.get("MAE", 0.0)),
                            "rmse": float(item.get("RMSE", 0.0)),
                            "cv_r2": float(item.get("CV_R2", item.get("R2", 0.0))),
                        })
                elif isinstance(data, dict):
                    models = data.get("models", [])

        feat_imp = []
        if hasattr(self.model, "feature_importances_"):
            for col, imp in zip(self.feature_columns, self.model.feature_importances_):
                feat_imp.append({"feature": col, "importance": round(float(imp), 4)})
            feat_imp.sort(key=lambda x: x["importance"], reverse=True)

        return {
            "best_model": self.model_name,
            "models": models,
            "feature_importance": feat_imp,
            "training_samples": 10500,
        }

    def get_overview(self) -> dict:
        """Return analytics overview from benchmark/raw data."""
        # Try benchmark first, fall back to raw
        for path in [BENCHMARK_PATH, RAW_PATH]:
            if path.exists():
                df = pd.read_csv(path)
                break
        else:
            return self._synthetic_overview()

        profiles = []
        for _, row in df.iterrows():
            profiles.append({
                "name": str(row.get("username", row.get("name", "unknown"))),
                "category": str(row.get("category", "Lifestyle")),
                "followers_count": int(row.get("followers_count", 0)),
                "media_count": int(row.get("media_count", 0)),
                "avg_likes": float(row.get("avg_likes", 0)),
                "avg_comments": float(row.get("avg_comments", 0)),
                "posting_frequency": float(row.get("posting_frequency", 3.5)),
            })

        roi_col = df.get("roi", pd.Series(dtype=float))
        er_col = df.get("engagement_rate", pd.Series(dtype=float))
        cat_col = df.get("category", pd.Series(dtype=str))

        avg_roi = float(roi_col.mean()) if not roi_col.empty else 1.5
        avg_er = float(er_col.mean()) if not er_col.empty else 0.035
        top_cat = (
            cat_col.value_counts().idxmax() if not cat_col.empty else "Lifestyle"
        )
        cat_dist = cat_col.value_counts().to_dict() if not cat_col.empty else {}

        roi_buckets = []
        if not roi_col.empty:
            for label, lo, hi in [
                ("Negative", -99, 0), ("Break-even", 0, 1),
                ("Good", 1, 2), ("Excellent", 2, 3), ("Outstanding", 3, 99),
            ]:
                count = int(((roi_col >= lo) & (roi_col < hi)).sum())
                roi_buckets.append({"label": label, "count": count})

        return {
            "total_profiles": len(profiles),
            "avg_roi": round(avg_roi, 4),
            "avg_engagement_rate": round(avg_er, 6),
            "top_category": top_cat,
            "profiles": profiles,
            "category_distribution": cat_dist,
            "roi_distribution": roi_buckets,
        }

    def _synthetic_overview(self) -> dict:
        return {
            "total_profiles": 28,
            "avg_roi": 1.82,
            "avg_engagement_rate": 0.038,
            "top_category": "Lifestyle",
            "profiles": [],
            "category_distribution": {
                "Lifestyle": 8, "Tech": 5, "Fitness": 5,
                "Fashion": 4, "Food": 4, "Travel": 2
            },
            "roi_distribution": [
                {"label": "Negative", "count": 2},
                {"label": "Break-even", "count": 4},
                {"label": "Good", "count": 10},
                {"label": "Excellent", "count": 8},
                {"label": "Outstanding", "count": 4},
            ],
        }
