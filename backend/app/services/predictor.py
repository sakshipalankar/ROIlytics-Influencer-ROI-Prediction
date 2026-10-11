"""ML inference service — loads best_model.pkl once at startup and serves predictions.

The model pickle contains: model (RandomForestRegressor), scaler (StandardScaler),
model_name, feature_columns.  The scaler is applied at inference in feature_columns order.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Path resolution: backend is at project_root/backend, models at project_root/models
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # backend/app/services -> project root
MODEL_PATH = PROJECT_ROOT / "models" / "best_model.pkl"
RESULTS_PATH = PROJECT_ROOT / "models" / "model_results.json"

from .constants import CATEGORY_MAP, BUCKET_MAP, CATEGORY_ER_BENCHMARKS


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
        self.scaler = data.get("scaler")  # StandardScaler — apply before predict
        self.feature_columns: list[str] = data["feature_columns"]
        self.model_name: str = data.get("model_name", "Random Forest")
        logger.info(
            "Loaded model: %s | features: %s | scaler: %s",
            self.model_name, self.feature_columns,
            type(self.scaler).__name__ if self.scaler else "None",
        )

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
        # Apply scaler if present (trained with StandardScaler)
        if self.scaler is not None:
            X = pd.DataFrame(self.scaler.transform(X), columns=self.feature_columns)

        roi = float(self.model.predict(X)[0])
        revenue = spend * (1 + roi)
        profit = revenue - spend
        engagement_rate = (avg_likes + avg_comments) / max(followers_count, 1)
        tier, tier_color = _tier_label(roi)
        return {
            "estimated_roi": round(roi, 4),
            "roi": round(roi, 4),  # backward compat
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
        training_samples: int | None = None

        if RESULTS_PATH.exists():
            with open(RESULTS_PATH) as f:
                data = json.load(f)
                if isinstance(data, list):
                    training_samples = len(data) if not any("Model" in (d if isinstance(d, dict) else {}) for d in data) else None
                    for item in data:
                        if isinstance(item, dict) and "Model" in item:
                            models.append({
                                "name": str(item.get("Model", "Unknown")),
                                "r2": float(item.get("R2", 0.0)),
                                "mae": float(item.get("MAE", 0.0)),
                                "rmse": float(item.get("RMSE", 0.0)),
                                "cv_r2": float(item.get("CV_R2", item.get("R2", 0.0))),
                            })
                elif isinstance(data, dict):
                    models = data.get("models", [])
                    training_samples = data.get("training_samples")

        feat_imp = []
        if hasattr(self.model, "feature_importances_"):
            for col, imp in zip(self.feature_columns, self.model.feature_importances_):
                feat_imp.append({"feature": col, "importance": round(float(imp), 4)})
            feat_imp.sort(key=lambda x: x["importance"], reverse=True)

        return {
            "best_model": self.model_name,
            "models": models,
            "feature_importance": feat_imp,
            "training_samples": training_samples,
        }

    def get_overview(self) -> dict:
        """Build analytics overview from clean scraped data (influencers.db / influencers_clean.csv)."""
        csv_path = PROJECT_ROOT / "data" / "influencers_clean.csv"
        db_path = PROJECT_ROOT / "data" / "influencers.db"

        profiles_data: list[dict[str, Any]] = []

        # Try SQLite database first
        if db_path.exists():
            import sqlite3
            try:
                conn = sqlite3.connect(str(db_path))
                conn.row_factory = sqlite3.Row
                rows = conn.execute("SELECT * FROM influencers WHERE (is_brand = 0 OR is_brand IS NULL) AND (er_suspect = 0 OR er_suspect IS NULL)").fetchall()
                profiles_data = [dict(r) for r in rows]
                conn.close()
            except Exception as e:
                logger.warning(f"Could not read influencers.db for overview: {e}")

        # Fallback to CSV if DB empty
        if not profiles_data and csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                if "is_brand" in df.columns:
                    df = df[(df["is_brand"] == 0) | (df["is_brand"].isna())]
                if "er_suspect" in df.columns:
                    df = df[(df["er_suspect"] == 0) | (df["er_suspect"].isna())]
                profiles_data = df.to_dict(orient="records")
            except Exception as e:
                logger.warning(f"Could not read influencers_clean.csv for overview: {e}")

        if not profiles_data:
            return {
                "total_profiles": 0,
                "avg_roi": 0.0,
                "avg_engagement_rate": 0.0,
                "top_category": "—",
                "profiles": [],
                "category_distribution": {},
                "roi_distribution": [],
            }

        profiles = []
        roi_values = []
        er_values = []
        categories: list[str] = []

        for p in profiles_data:
            posting_freq = p.get("posting_frequency") or 3.5
            profiles.append({
                "name": p.get("username", "unknown"),
                "category": p.get("category") or "Uncategorised",
                "followers_count": int(p.get("followers_count") or 0),
                "media_count": int(p.get("media_count") or 0),
                "avg_likes": float(p.get("avg_likes") or 0),
                "avg_comments": float(p.get("avg_comments") or 0),
                "posting_frequency": float(posting_freq),
            })

            er = float(p.get("engagement_rate") or 0.0)
            er_values.append(er)
            cat = p.get("category") or "Uncategorised"
            categories.append(cat)

            roi_val = p.get("roi")
            if roi_val is not None:
                roi_values.append(float(roi_val))
            else:
                # Compute estimated ROI fallback
                try:
                    result = self.predict(
                        followers_count=int(p.get("followers_count") or 0),
                        media_count=int(p.get("media_count") or 0),
                        avg_likes=float(p.get("avg_likes") or 0),
                        avg_comments=float(p.get("avg_comments") or 0),
                        category=cat if cat in CATEGORY_MAP else "Lifestyle",
                        posting_frequency=float(posting_freq),
                        spend=float(p.get("spend") or 5000),
                    )
                    roi_values.append(result["roi"])
                except Exception:
                    roi_values.append(0.0)

        avg_roi = sum(roi_values) / len(roi_values) if roi_values else 0.0
        avg_er = sum(er_values) / len(er_values) if er_values else 0.0

        # Category distribution
        cat_dist: dict[str, int] = {}
        for c in categories:
            cat_dist[c] = cat_dist.get(c, 0) + 1
        top_cat = max(cat_dist, key=cat_dist.get) if cat_dist else "—"  # type: ignore[arg-type]

        # ROI distribution buckets
        roi_buckets = []
        if roi_values:
            for label, lo, hi in [
                ("Negative", -99, 0), ("Break-even", 0, 1),
                ("Good", 1, 2), ("Excellent", 2, 3), ("Outstanding", 3, 99),
            ]:
                count = sum(1 for r in roi_values if lo <= r < hi)
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
