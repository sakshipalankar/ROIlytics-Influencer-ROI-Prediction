import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  PredictResponse, AnalyticsOverview, ModelResultsResponse,
  CreatorProfile, BrandProfile, InfluencerCard, ShortlistItem, DatasetStats,
} from '../types';

// ─── Auth ─────────────────────────────────────────────────────────────────────
export interface AuthUser {
  username: string;
  email: string;
  avatarColor: string;
  joinedAt: string;
}

const AVATAR_COLORS = [
  '#6366f1','#8b5cf6','#10b981','#f59e0b','#f43f5e',
  '#38bdf8','#ec4899','#14b8a6','#f97316','#84cc16',
];
const pickColor = (seed?: string): string => {
  if (!seed || seed.length === 0) return AVATAR_COLORS[0];
  return AVATAR_COLORS[Math.abs(seed.charCodeAt(0)) % AVATAR_COLORS.length];
};

// ─── State Interface ───────────────────────────────────────────────────────────
interface AppState {
  // Auth
  user: AuthUser | null;
  setUser: (u: AuthUser | null) => void;
  logout: () => void;

  // Sidebar
  sidebarOpen: boolean;
  setSidebarOpen: (v: boolean) => void;
  toggleSidebar: () => void;

  // Navigation
  activePage: string;
  setActivePage: (p: string) => void;

  // Prediction
  predictionResult: PredictResponse | null;
  setPredictionResult: (r: PredictResponse | null) => void;
  isPredicting: boolean;
  setIsPredicting: (v: boolean) => void;

  // Analytics
  overview: AnalyticsOverview | null;
  setOverview: (o: AnalyticsOverview) => void;

  // Model results
  modelResults: ModelResultsResponse | null;
  setModelResults: (m: ModelResultsResponse) => void;

  // Selected preset creator
  selectedPreset: CreatorProfile | null;
  setSelectedPreset: (p: CreatorProfile | null) => void;

  // Brand profile (discovery)
  brandProfile: BrandProfile;
  setBrandProfile: (p: BrandProfile) => void;

  // Discovery results
  discoveryResults: InfluencerCard[];
  setDiscoveryResults: (r: InfluencerCard[]) => void;
  isDiscovering: boolean;
  setIsDiscovering: (v: boolean) => void;

  // Dataset stats
  datasetStats: DatasetStats | null;
  setDatasetStats: (s: DatasetStats) => void;

  // Shortlist
  shortlist: ShortlistItem[];
  addToShortlist: (inf: InfluencerCard) => void;
  removeFromShortlist: (id: number) => void;
  clearShortlist: () => void;

  // Detail modal
  detailInfluencer: InfluencerCard | null;
  setDetailInfluencer: (inf: InfluencerCard | null) => void;
}

const DEFAULT_BRAND: BrandProfile = {
  brand_name: '',
  category: 'Fitness',
  budget: 5000,
  goal: 'awareness',
  country: 'All',
  min_followers: 0,
  max_followers: 999999999,
  min_er: 0,
  follower_tier: 'All',
  is_verified: null,
  limit: 20,
  offset: 0,
  sort_by: 'fit_score',
};

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Auth
      user: null,
      setUser: (u) => set({ user: u }),
      logout: () => set({ user: null, shortlist: [], discoveryResults: [] }),

      // Sidebar
      sidebarOpen: true,
      setSidebarOpen: (v) => set({ sidebarOpen: v }),
      toggleSidebar: () => set(s => ({ sidebarOpen: !s.sidebarOpen })),

      // Navigation
      activePage: 'discover',
      setActivePage: (p) => set({ activePage: p }),

      // Prediction
      predictionResult: null,
      setPredictionResult: (r) => set({ predictionResult: r }),
      isPredicting: false,
      setIsPredicting: (v) => set({ isPredicting: v }),

      // Analytics
      overview: null,
      setOverview: (o) => set({ overview: o }),

      // Model results
      modelResults: null,
      setModelResults: (m) => set({ modelResults: m }),

      // Selected preset
      selectedPreset: null,
      setSelectedPreset: (p) => set({ selectedPreset: p }),

      // Brand profile
      brandProfile: DEFAULT_BRAND,
      setBrandProfile: (p) => set({ brandProfile: p }),

      // Discovery
      discoveryResults: [],
      setDiscoveryResults: (r) => set({ discoveryResults: r }),
      isDiscovering: false,
      setIsDiscovering: (v) => set({ isDiscovering: v }),

      // Dataset stats
      datasetStats: null,
      setDatasetStats: (s) => set({ datasetStats: s }),

      // Shortlist
      shortlist: [],
      addToShortlist: (inf) => {
        const { shortlist } = get();
        if (shortlist.length >= 5 || shortlist.find(s => s.id === inf.id)) return;
        set({ shortlist: [...shortlist, { ...inf, addedAt: Date.now() }] });
      },
      removeFromShortlist: (id) =>
        set(s => ({ shortlist: s.shortlist.filter(x => x.id !== id) })),
      clearShortlist: () => set({ shortlist: [] }),

      // Detail modal
      detailInfluencer: null,
      setDetailInfluencer: (inf) => set({ detailInfluencer: inf }),
    }),
    {
      name: 'roilytics-store',
      // Only persist auth + sidebar state
      partialize: (s) => ({
        user: s.user,
        sidebarOpen: s.sidebarOpen,
        shortlist: s.shortlist,
        brandProfile: s.brandProfile,
      }),
    }
  )
);

export { pickColor };
