import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import type { BrandProfile, Category, FollowerTier, CampaignGoal } from '../../types';
import { Zap } from 'lucide-react';

const CATEGORIES: Category[] = [
  'Fitness', 'Fashion', 'Tech', 'Food', 'Travel',
  'Lifestyle', 'Beauty', 'Gaming', 'Finance', 'Education',
];

const CATEGORY_EMOJIS: Record<string, string> = {
  Fitness: '💪', Fashion: '👗', Tech: '💻', Food: '🍕', Travel: '✈️',
  Lifestyle: '🌿', Beauty: '💄', Gaming: '🎮', Finance: '📈', Education: '📚',
};

const GOALS: { value: CampaignGoal; label: string; desc: string; icon: string }[] = [
  { value: 'awareness',  label: 'Brand Awareness',  desc: 'Maximize reach & impressions', icon: '📢' },
  { value: 'engagement', label: 'Engagement',        desc: 'Drive likes & comments',       icon: '❤️' },
  { value: 'sales',      label: 'Sales & ROI',       desc: 'Maximize revenue multiplier',  icon: '💰' },
];

const TIERS: { value: FollowerTier; label: string }[] = [
  { value: 'All',   label: 'All Tiers' },
  { value: 'Nano',  label: 'Nano (1K–10K)' },
  { value: 'Micro', label: 'Micro (10K–100K)' },
  { value: 'Macro', label: 'Macro (100K–1M)' },
  { value: 'Mega',  label: 'Mega (1M+)' },
];

const COUNTRIES = [
  { value: 'All', label: '🌍 All Countries' },
  { value: 'US',  label: '🇺🇸 United States' },
  { value: 'IN',  label: '🇮🇳 India' },
  { value: 'GB',  label: '🇬🇧 United Kingdom' },
  { value: 'CA',  label: '🇨🇦 Canada' },
  { value: 'AU',  label: '🇦🇺 Australia' },
  { value: 'DE',  label: '🇩🇪 Germany' },
  { value: 'FR',  label: '🇫🇷 France' },
  { value: 'BR',  label: '🇧🇷 Brazil' },
  { value: 'JP',  label: '🇯🇵 Japan' },
];

const BUDGET_PRESETS = [5000, 25000, 50000, 100000, 250000];

interface Props {
  onSearch: () => void;
}

const BrandSetupForm: React.FC<Props> = ({ onSearch }) => {
  const { brandProfile, setBrandProfile, isDiscovering } = useAppStore();

  const update = (patch: Partial<BrandProfile>) =>
    setBrandProfile({ ...brandProfile, ...patch });

  return (
    <div className="brand-setup-hub">
      {/* 2-Column Responsive Form Layout */}
      <div className="bsh-grid">
        {/* Left Column: Brand & Category */}
        <div className="bsh-col">
          {/* Company / Brand Name */}
          <div className="bsh-field">
            <label className="bsh-label">Company / Brand Name</label>
            <input
              id="brand-name-input"
              className="form-input bsh-input"
              placeholder="e.g. etude, Nike, Boat, Sephora..."
              value={brandProfile.brand_name}
              onChange={e => update({ brand_name: e.target.value })}
            />
          </div>

          {/* Influencer Category */}
          <div className="bsh-field">
            <div className="bsh-field-header">
              <label className="bsh-label">Influencer Category</label>
              <span className="bsh-badge">{CATEGORY_EMOJIS[brandProfile.category] || '🏷️'} {brandProfile.category}</span>
            </div>
            <div className="bsh-cat-grid">
              {CATEGORIES.map(cat => (
                <button
                  key={cat}
                  id={`cat-${cat.toLowerCase()}`}
                  type="button"
                  onClick={() => update({ category: cat })}
                  className={`bsh-cat-btn${brandProfile.category === cat ? ' active' : ''}`}
                >
                  <span className="bsh-cat-emoji">{CATEGORY_EMOJIS[cat]}</span>
                  <span className="bsh-cat-name">{cat}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Goals & Budget */}
        <div className="bsh-col">
          {/* Campaign Goal */}
          <div className="bsh-field">
            <label className="bsh-label">Campaign Goal</label>
            <div className="bsh-goals-row">
              {GOALS.map(g => (
                <button
                  key={g.value}
                  id={`goal-${g.value}`}
                  type="button"
                  onClick={() => update({ goal: g.value })}
                  className={`bsh-goal-card${brandProfile.goal === g.value ? ' active' : ''}`}
                >
                  <span className="bsh-goal-icon">{g.icon}</span>
                  <div className="bsh-goal-info">
                    <span className="bsh-goal-title">{g.label}</span>
                    <span className="bsh-goal-desc">{g.desc}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Campaign Budget */}
          <div className="bsh-field">
            <div className="bsh-field-header">
              <label className="bsh-label">Campaign Budget</label>
              <span className="bsh-budget-display">
                Rs. {brandProfile.budget.toLocaleString('en-IN')}
              </span>
            </div>
            <input
              id="budget-slider"
              type="range"
              min={500} max={500000} step={500}
              value={brandProfile.budget}
              style={{ '--pct': `${Math.round(((brandProfile.budget - 500) / 499500) * 100)}%` } as React.CSSProperties}
              onChange={e => update({ budget: Number(e.target.value) })}
              className="bsh-range-slider"
            />
            {/* Presets */}
            <div className="bsh-presets-row">
              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Presets:</span>
              {BUDGET_PRESETS.map(p => (
                <button
                  key={p}
                  type="button"
                  onClick={() => update({ budget: p })}
                  className={`bsh-preset-chip${brandProfile.budget === p ? ' active' : ''}`}
                >
                  Rs. {p >= 1000 ? `${p / 1000}K` : p}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Targeting Filters Bar */}
      <div className="bsh-filters-bar">
        <div className="bsh-filter-item">
          <label className="bsh-filter-label">Follower Tier</label>
          <select
            id="tier-select"
            className="form-select bsh-select"
            value={brandProfile.follower_tier}
            onChange={e => update({ follower_tier: e.target.value as any })}
          >
            {TIERS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
          </select>
        </div>

        <div className="bsh-filter-item">
          <label className="bsh-filter-label">Country</label>
          <select
            id="country-select"
            className="form-select bsh-select"
            value={brandProfile.country}
            onChange={e => update({ country: e.target.value })}
          >
            {COUNTRIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
        </div>

        <div className="bsh-filter-item">
          <label className="bsh-filter-label">Sort Results By</label>
          <select
            id="sort-by-select"
            className="form-select bsh-select"
            value={brandProfile.sort_by}
            onChange={e => update({ sort_by: e.target.value as any })}
          >
            <option value="fit_score">🎯 Fit Score (Recommended)</option>
            <option value="roi">💰 Predicted ROI</option>
            <option value="engagement_rate">❤️ Engagement Rate</option>
            <option value="followers">👥 Followers</option>
          </select>
        </div>

        <div className="bsh-filter-item bsh-check-item">
          <label className="bsh-checkbox-label">
            <input
              type="checkbox"
              id="verified-check"
              checked={brandProfile.is_verified === true}
              onChange={e => update({ is_verified: e.target.checked ? true : null })}
              className="bsh-checkbox"
            />
            <span>Verified accounts only ✓</span>
          </label>
        </div>
      </div>

      {/* Action CTA Button */}
      <div className="bsh-action-row">
        <button
          id="find-influencers-btn"
          className="btn btn-primary bsh-submit-btn"
          onClick={onSearch}
          disabled={isDiscovering || !brandProfile.category}
        >
          {isDiscovering ? (
            <><div className="spinner" style={{ width: 18, height: 18 }} /> Scoring 10,500+ Influencers…</>
          ) : (
            <><Zap size={18} /> Find My Top Influencers</>
          )}
        </button>
      </div>
    </div>
  );
};

export default BrandSetupForm;

