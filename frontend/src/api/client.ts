import axios from 'axios';
import type {
  PredictRequest, PredictResponse,
  SimulateResponse, AnalyticsOverview, ModelResultsResponse,
  InstagramProfile, BrandProfile, DiscoverResponse,
  DatasetStats, InfluencerCard,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// ─── Prediction ────────────────────────────────────────────────────────────
export const predictSingle = async (body: PredictRequest): Promise<PredictResponse> => {
  const { data } = await api.post<PredictResponse>('/predict', body);
  return data;
};

export const simulateBudget = async (
  params: PredictRequest & { spend_min: number; spend_max: number; steps?: number }
): Promise<SimulateResponse> => {
  const { spend, ...rest } = params;
  const { data } = await api.get<SimulateResponse>('/predict/simulate', { params: rest });
  return data;
};

export const predictBatch = async (file: File): Promise<Blob> => {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post<Blob>('/predict/batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    responseType: 'blob',
  });
  return data;
};

// ─── Analytics ─────────────────────────────────────────────────────────────
export const getAnalyticsOverview = async (): Promise<AnalyticsOverview> => {
  const { data } = await api.get<AnalyticsOverview>('/analytics/overview');
  return data;
};

// ─── Model Results ──────────────────────────────────────────────────────────
export const getModelResults = async (): Promise<ModelResultsResponse> => {
  const { data } = await api.get<ModelResultsResponse>('/models/results');
  return data;
};

// ─── Instagram ──────────────────────────────────────────────────────────────
export const fetchInstagramProfile = async (
  username: string, access_token: string
): Promise<InstagramProfile> => {
  const { data } = await api.post<InstagramProfile>('/instagram/fetch', { username, access_token });
  return data;
};

// ─── Discovery ──────────────────────────────────────────────────────────────
export const discoverInfluencers = async (brand: BrandProfile): Promise<DiscoverResponse> => {
  const { data } = await api.post<DiscoverResponse>('/discover', brand);
  return data;
};

export const getDatasetStats = async (): Promise<DatasetStats> => {
  const { data } = await api.get<DatasetStats>('/discover/stats');
  return data;
};

export const getInfluencerById = async (id: number): Promise<InfluencerCard & Record<string, any>> => {
  const { data } = await api.get(`/discover/influencer/${id}`);
  return data;
};

export const compareInfluencers = async (
  ids: number[], budget: number, goal: string
): Promise<{ influencers: InfluencerCard[]; budget: number; goal: string }> => {
  const { data } = await api.post('/discover/compare', {
    influencer_ids: ids,
    budget,
    goal,
  });
  return data;
};
