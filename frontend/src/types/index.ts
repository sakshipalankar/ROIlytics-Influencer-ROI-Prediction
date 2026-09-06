// All TypeScript interfaces for ROIlytics frontend

// ─── Prediction (legacy) ───────────────────────────────────────────────────
export interface PredictRequest {
  followers_count: number;
  media_count: number;
  avg_likes: number;
  avg_comments: number;
  category: string;
  posting_frequency: number;
  spend: number;
}

export interface PredictResponse {
  roi: number;
  tier: string;
  tier_color: string;
  predicted_revenue: number;
  predicted_profit: number;
  engagement_rate: number;
  follower_tier: string;
}

export interface SimulatePoint {
  spend: number;
  revenue: number;
  profit: number;
  roi: number;
}

export interface SimulateResponse {
  points: SimulatePoint[];
}

export interface CreatorProfile {
  name: string;
  category: string;
  followers_count: number;
  media_count: number;
  avg_likes: number;
  avg_comments: number;
  posting_frequency: number;
}

export interface AnalyticsOverview {
  total_profiles: number;
  avg_roi: number;
  avg_engagement_rate: number;
  top_category: string;
  profiles: CreatorProfile[];
  category_distribution: Record<string, number>;
  roi_distribution: Array<{ label: string; count: number }>;
}

export interface ModelMetric {
  name: string;
  r2: number;
  mae: number;
  rmse: number;
  cv_r2: number;
}

export interface FeatureImportance {
  feature: string;
  importance: number;
}

export interface ModelResultsResponse {
  best_model: string;
  models: ModelMetric[];
  feature_importance: FeatureImportance[];
  training_samples: number;
}

export interface InstagramProfile {
  username: string;
  followers_count: number;
  media_count: number;
  biography: string | null;
  avg_likes: number;
  avg_comments: number;
  profile_picture_url: string | null;
  website: string | null;
}

// ─── Influencer Discovery ──────────────────────────────────────────────────
export type Category =
  | 'All' | 'Fitness' | 'Fashion' | 'Tech' | 'Food'
  | 'Travel' | 'Lifestyle' | 'Beauty' | 'Gaming' | 'Finance' | 'Education';

export type FollowerTier = 'All' | 'Nano' | 'Micro' | 'Macro' | 'Mega';
export type CampaignGoal = 'awareness' | 'engagement' | 'sales';
export type SortBy = 'fit_score' | 'roi' | 'followers' | 'engagement_rate';

export interface BrandProfile {
  brand_name: string;
  category: Category;
  budget: number;
  goal: CampaignGoal;
  country: string;
  min_followers: number;
  max_followers: number;
  min_er: number;
  follower_tier: FollowerTier;
  is_verified: boolean | null;
  limit: number;
  offset: number;
  sort_by: SortBy;
}

export interface InfluencerCard {
  id: number;
  username: string;
  full_name: string;
  category: string;
  sub_category: string;
  biography: string;
  followers_count: number;
  avg_likes: number;
  avg_comments: number;
  engagement_rate: number;
  posting_frequency: number;
  estimated_reach: number;
  is_verified: boolean;
  country: string;
  follower_tier: FollowerTier;
  audience_female_pct: number;
  audience_male_pct: number;
  audience_age_18_24?: number;
  audience_age_25_34?: number;
  audience_age_35_44?: number;
  fit_score: number;
  roi: number;
  spend: number;
  revenue: number;
  profile_pic_url: string;
}

export interface DiscoverResponse {
  influencers: InfluencerCard[];
  total_found: number;
  category: string;
  budget_tier: string;
}

export interface DatasetStats {
  total: number;
  avg_roi: number;
  avg_engagement_rate: number;
  verified_count: number;
  categories: string[];
  countries: string[];
  category_distribution: Record<string, number>;
  tier_distribution: Record<string, number>;
  db_engine?: string;
  db_host?: string;
}

export interface ShortlistItem extends InfluencerCard {
  addedAt: number;
}
