"""Pydantic v2 schemas for all API endpoints."""
from typing import Optional, List
from pydantic import BaseModel, Field


# ─── Prediction ───────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    followers_count: int = Field(..., ge=1000, le=500_000_000)
    media_count: int = Field(..., ge=1, le=100_000)
    avg_likes: float = Field(..., ge=0)
    avg_comments: float = Field(..., ge=0)
    category: str = Field(..., example="Tech")
    posting_frequency: float = Field(..., ge=0, le=30)
    spend: float = Field(..., ge=100, le=10_000_000)


class PredictResponse(BaseModel):
    roi: float
    tier: str
    tier_color: str
    predicted_revenue: float
    predicted_profit: float
    engagement_rate: float
    follower_tier: str


class SimulatePoint(BaseModel):
    spend: float
    revenue: float
    profit: float
    roi: float


class SimulateResponse(BaseModel):
    points: List[SimulatePoint]


# ─── Analytics ────────────────────────────────────────────────────────────────

class CreatorProfile(BaseModel):
    name: str
    category: str
    followers_count: int
    media_count: int
    avg_likes: float
    avg_comments: float
    posting_frequency: float


class AnalyticsOverview(BaseModel):
    total_profiles: int
    avg_roi: float
    avg_engagement_rate: float
    top_category: str
    profiles: List[CreatorProfile]
    category_distribution: dict
    roi_distribution: List[dict]


# ─── Model Results ────────────────────────────────────────────────────────────

class ModelMetric(BaseModel):
    name: str
    r2: float
    mae: float
    rmse: float
    cv_r2: float


class ModelResultsResponse(BaseModel):
    best_model: str
    models: List[ModelMetric]
    feature_importance: List[dict]
    training_samples: int


# ─── Instagram ────────────────────────────────────────────────────────────────

class InstagramFetchRequest(BaseModel):
    username: str
    access_token: str


class InstagramProfile(BaseModel):
    username: str
    followers_count: int
    media_count: int
    biography: Optional[str] = None
    avg_likes: float
    avg_comments: float
    profile_picture_url: Optional[str] = None
    website: Optional[str] = None


# ─── Influencer Discovery ─────────────────────────────────────────────────────

class BrandProfileRequest(BaseModel):
    brand_name: str = Field(..., example="Nike")
    category: str = Field(..., example="Fitness")
    budget: float = Field(..., ge=200, le=10_000_000, example=5000)
    goal: str = Field("awareness", example="awareness")  # awareness | engagement | sales
    country: Optional[str] = Field(None, example="IN")
    min_followers: int = Field(0, ge=0)
    max_followers: int = Field(999_999_999, ge=0)
    min_er: float = Field(0.0, ge=0.0)
    follower_tier: Optional[str] = Field(None)  # Nano | Micro | Macro | Mega | All
    is_verified: Optional[bool] = Field(None)
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)
    sort_by: str = Field("fit_score")  # fit_score | roi | followers | engagement_rate


class InfluencerCard(BaseModel):
    id: int
    username: str
    full_name: str
    category: str
    sub_category: str
    biography: str
    followers_count: int
    avg_likes: float
    avg_comments: float
    engagement_rate: float
    posting_frequency: float
    estimated_reach: int
    is_verified: bool
    country: str
    follower_tier: str
    audience_female_pct: float
    audience_male_pct: float
    fit_score: float
    roi: float
    spend: float
    revenue: float
    profile_pic_url: str


class DiscoverResponse(BaseModel):
    influencers: List[InfluencerCard]
    total_found: int
    category: str
    budget_tier: str


class DatasetStats(BaseModel):
    total: int
    avg_roi: float
    avg_engagement_rate: float
    verified_count: int
    categories: List[str]
    countries: List[str]
    category_distribution: dict
    tier_distribution: dict
    db_engine: Optional[str] = "sqlite"
    db_host: Optional[str] = None


class ShortlistCompareRequest(BaseModel):
    influencer_ids: List[int] = Field(..., min_length=2, max_length=5)
    budget: float = Field(..., ge=200)
    goal: str = Field("awareness")
