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
  min_followers: number;
  max_followers: number;
  min_er: number;
  limit: number;
  offset: number;
  sort_by: SortBy;
}

export interface InfluencerCard {
  id?: number;
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
  audience_female_pct?: number | null;
  audience_male_pct?: number | null;
  audience_age_18_24?: number;
  audience_age_25_34?: number;
  audience_age_35_44?: number;
  fit_score: number;
  roi: number | null;
  spend: number | null;
  revenue: number | null;
  profile_pic_url: string;
  profile_url?: string;
  profile_screenshot?: string;
  roi_source?: string;
  is_brand?: number;
  er_suspect?: number;
  source: string;
  reliable: boolean;
  warnings: string[];
  note?: string;
  is_verified?: boolean;
  country?: string;
  follower_tier?: string;
  fetched_at?: string;
}

export interface DiscoverResponse {
  influencers: InfluencerCard[];
  unreliable_influencers: InfluencerCard[];
  total_found: number;
  category: string;
  budget_tier: string;
  notice?: string;
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

// ─── Authentication & User Types ─────────────────────────────────────────────
export interface AuthUser {
  id?: number;
  username: string;
  name?: string;
  email: string;
  avatar_url?: string;
  avatar?: string;
  provider?: string;
  role?: string;
  company?: string;
  created_at?: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  password: string;
  role?: string;
  company?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface GoogleAuthPayload {
  email: string;
  name: string;
  picture?: string;
}

export interface UpdateProfilePayload {
  email: string;
  username: string;
  role?: string;
  avatar_url?: string;
}

export interface ChangePasswordPayload {
  email: string;
  current_password: string;
  new_password: string;
}
