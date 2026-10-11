"""Pydantic v2 schemas for all API endpoints."""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone


# ─── Prediction ───────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    followers_count: int = Field(..., ge=1, le=500_000_000)
    media_count: int = Field(..., ge=1, le=100_000)
    avg_likes: float = Field(..., ge=0)
    avg_comments: float = Field(..., ge=0)
    category: str = Field(...)
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


# ─── Live Accounts & Analysis ──────────────────────────────────────────────────

class AddAccountRequest(BaseModel):
    label: str
    token: str

class LiveAccount(BaseModel):
    id: int
    label: str
    username: Optional[str] = None
    token_updated_at: str
    token_expires_at: Optional[str] = None
    last_error: Optional[str] = None

class LiveAnalyzeRequest(BaseModel):
    account_id: int
    category: str = Field("Lifestyle")
    spend: float = Field(5000.0, ge=100)

class LiveAnalyzeResponse(BaseModel):
    profile: dict
    features: dict
    warnings: List[str]
    estimated_roi: Optional[float]
    tier: str
    predicted_revenue: Optional[float]
    predicted_profit: Optional[float]
    fetched_at: str
    from_cache: bool
    reliable: bool = True
    reliability_note: Optional[str] = None
    source: str = "official"
    note: Optional[str] = None

class AnalyzeAllRequest(BaseModel):
    category: str = Field("Lifestyle")
    spend: float = Field(5000.0, ge=100)

class AnalyzeAllResponse(BaseModel):
    results: List[dict]


# ─── Public Lookup ────────────────────────────────────────────────────────────

class PublicLookupRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=30, pattern=r"^[a-zA-Z0-9._]+$")
    category: str = Field("Lifestyle")
    spend: float = Field(5000.0, ge=100)

class SnapshotPost(BaseModel):
    like_count: Optional[int] = Field(None, ge=0)
    comments_count: Optional[int] = Field(None, ge=0)
    timestamp: Optional[str] = None
    
    @field_validator('timestamp')
    @classmethod
    def check_timestamp(cls, v: str) -> str:
        try:
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError('timestamp must be a valid ISO-8601 string')
        if dt > datetime.now(timezone.utc):
            raise ValueError('timestamp cannot be in the future')
        return v

class PublicSnapshotRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=30, pattern=r"^[a-zA-Z0-9._]+$")
    category: str = Field("Lifestyle")
    followers_count: int = Field(..., ge=1)
    media_count: int = Field(..., ge=1)
    biography: Optional[str] = None
    posts: List[SnapshotPost] = Field(..., min_length=1)
    spend: float = Field(5000.0, ge=100)
    collected_at: Optional[str] = None
    collected_note: Optional[str] = Field(None, max_length=200)

class PublicLookupResponse(BaseModel):
    profile: dict
    features: dict
    warnings: List[str]
    estimated_roi: Optional[float]
    tier: str
    predicted_revenue: Optional[float]
    predicted_profit: Optional[float]
    fetched_at: str
    from_cache: bool
    reliable: bool = True
    reliability_note: Optional[str] = None
    source: str
    note: Optional[str] = None

class WatchlistAddRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=30, pattern=r"^[a-zA-Z0-9._]+$")
    category: str

class WatchlistRefreshRequest(BaseModel):
    category: Optional[str] = None
    spend: float = Field(5000.0, ge=100)

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


# ─── Influencer Discovery ─────────────────────────────────────────────────────

class BrandProfileRequest(BaseModel):
    brand_name: Optional[str] = Field("My Brand")
    category: Optional[str] = Field("Fitness")
    budget: float = Field(5000.0, ge=100, le=10_000_000)
    goal: Optional[str] = Field("awareness")  # awareness | engagement | sales
    min_followers: int = Field(0, ge=0)
    max_followers: int = Field(999_999_999, ge=0)
    min_er: float = Field(0.0, ge=0.0)
    limit: int = Field(30, ge=1, le=100)
    offset: int = Field(0, ge=0)
    sort_by: Optional[str] = Field("fit_score")  # fit_score | roi | followers | engagement_rate


class InfluencerCard(BaseModel):
    id: Optional[int] = None
    username: str
    full_name: str
    category: str
    sub_category: Optional[str] = ""
    biography: Optional[str] = ""
    followers_count: int
    avg_likes: float
    avg_comments: float
    engagement_rate: float
    posting_frequency: float
    estimated_reach: Optional[int] = 0
    audience_female_pct: Optional[float] = None
    audience_male_pct: Optional[float] = None
    fit_score: float
    roi: Optional[float]
    spend: float
    revenue: Optional[float]
    profile_pic_url: str
    profile_url: Optional[str] = None
    profile_screenshot: Optional[str] = None
    roi_source: Optional[str] = "model_estimate"
    is_brand: int = 0
    er_suspect: int = 0
    source: str = "official"
    reliable: bool = True
    warnings: List[str] = []
    fetched_at: Optional[str] = None
    collected_at: Optional[str] = None
    collected_note: Optional[str] = None


class DiscoverResponse(BaseModel):
    influencers: List[InfluencerCard]
    unreliable_influencers: List[InfluencerCard] = []
    total_found: int
    category: str
    budget_tier: str
    notice: Optional[str] = None


class DatasetStats(BaseModel):
    total: int
    avg_roi: float
    avg_engagement_rate: float
    categories: List[str]
    category_distribution: dict
    db_engine: Optional[str] = "sqlite"
    db_host: Optional[str] = None


class ShortlistCompareRequest(BaseModel):
    influencer_ids: List[int] = Field(..., min_length=2, max_length=5)
    budget: float = Field(..., ge=200)
    goal: str = Field("awareness")


# ─── User Authentication & Management ──────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=150)
    password: str = Field(..., min_length=6)
    role: Optional[str] = "Campaign Manager"


class UserLoginRequest(BaseModel):
    email: str
    password: str


class GoogleAuthRequest(BaseModel):
    email: str
    name: str
    picture: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: Optional[int] = None
    username: str
    email: str
    avatar_url: Optional[str] = None
    provider: str = "email"
    role: str = "Campaign Manager"
    created_at: Optional[str] = None


class UpdateProfileRequest(BaseModel):
    email: str
    username: str
    role: Optional[str] = None
    avatar_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    email: str
    current_password: str
    new_password: str
