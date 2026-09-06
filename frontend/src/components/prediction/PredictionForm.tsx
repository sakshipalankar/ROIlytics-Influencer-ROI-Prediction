import React, { useState, useEffect } from 'react';
import type { AnalyticsOverview, CreatorProfile } from '../../types';
import { predictSingle } from '../../api/client';
import { useAppStore } from '../../store/useAppStore';
import { Zap, RefreshCw } from 'lucide-react';

const CATEGORIES = ['Fitness', 'Fashion', 'Tech', 'Food', 'Travel', 'Lifestyle'];

interface Props {
  overview: AnalyticsOverview | null;
}

const DEFAULT_FORM = {
  followers_count: 85000,
  media_count: 340,
  avg_likes: 3200,
  avg_comments: 95,
  category: 'Tech',
  posting_frequency: 3.5,
  spend: 4500,
};

function pct(val: number, min: number, max: number) {
  return Math.round(((val - min) / (max - min)) * 100);
}

const PredictionForm: React.FC<Props> = ({ overview }) => {
  const { setPredictionResult, setIsPredicting, isPredicting, setSelectedPreset } = useAppStore();
  const [form, setForm] = useState(DEFAULT_FORM);
  const [error, setError] = useState<string | null>(null);
  const [presetIdx, setPresetIdx] = useState<number>(-1);

  const profiles: CreatorProfile[] = overview?.profiles ?? [];

  useEffect(() => {
    if (presetIdx >= 0 && profiles[presetIdx]) {
      const p = profiles[presetIdx];
      setForm(prev => ({
        ...prev,
        followers_count: p.followers_count,
        media_count: p.media_count,
        avg_likes: p.avg_likes,
        avg_comments: p.avg_comments,
        category: p.category,
        posting_frequency: p.posting_frequency,
      }));
      setSelectedPreset(p);
    }
  }, [presetIdx]);

  const update = (key: keyof typeof form, val: number | string) =>
    setForm(prev => ({ ...prev, [key]: val }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsPredicting(true);
    try {
      const result = await predictSingle(form);
      setPredictionResult(result);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? err?.message ?? 'Prediction failed');
    } finally {
      setIsPredicting(false);
    }
  };

  const handleReset = () => {
    setForm(DEFAULT_FORM);
    setPresetIdx(-1);
    setPredictionResult(null);
    setSelectedPreset(null);
  };

  return (
    <form onSubmit={handleSubmit} id="prediction-form">
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <span className="card-title">⚡ Creator Preset</span>
        </div>
        <div className="card-body">
          <div className="form-group">
            <label className="form-label">Load a Real Creator Profile</label>
            <select
              id="preset-select"
              className="form-select"
              value={presetIdx}
              onChange={e => setPresetIdx(Number(e.target.value))}
            >
              <option value={-1}>— Manual entry —</option>
              {profiles.map((p, i) => (
                <option key={p.name} value={i}>
                  {p.name} ({p.category} · {p.followers_count.toLocaleString()} followers)
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">📊 Influencer Metrics</span>
        </div>
        <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

          {/* Followers */}
          <div className="range-group">
            <div className="range-header">
              <label className="form-label">Followers Count</label>
              <span className="range-value">{form.followers_count.toLocaleString()}</span>
            </div>
            <input
              id="followers-count-slider"
              type="range" min={1000} max={5000000} step={1000}
              value={form.followers_count}
              style={{ '--pct': `${pct(form.followers_count, 1000, 5000000)}%` } as React.CSSProperties}
              onChange={e => update('followers_count', Number(e.target.value))}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)' }}>
              <span>1K (Nano)</span><span>100K (Micro)</span><span>1M (Macro)</span><span>5M (Mega)</span>
            </div>
          </div>

          {/* Category & Frequency */}
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Category</label>
              <select
                id="category-select"
                className="form-select"
                value={form.category}
                onChange={e => update('category', e.target.value)}
              >
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="range-group">
              <div className="range-header">
                <label className="form-label">Posts / Week</label>
                <span className="range-value">{form.posting_frequency}</span>
              </div>
              <input
                id="posting-frequency-slider"
                type="range" min={0.5} max={14} step={0.5}
                value={form.posting_frequency}
                style={{ '--pct': `${pct(form.posting_frequency, 0.5, 14)}%` } as React.CSSProperties}
                onChange={e => update('posting_frequency', Number(e.target.value))}
              />
            </div>
          </div>

          {/* Avg Likes & Comments */}
          <div className="grid-2">
            <div className="range-group">
              <div className="range-header">
                <label className="form-label">Avg Likes / Post</label>
                <span className="range-value">{form.avg_likes.toLocaleString()}</span>
              </div>
              <input
                id="avg-likes-slider"
                type="range" min={10} max={500000} step={100}
                value={form.avg_likes}
                style={{ '--pct': `${pct(form.avg_likes, 10, 500000)}%` } as React.CSSProperties}
                onChange={e => update('avg_likes', Number(e.target.value))}
              />
            </div>
            <div className="range-group">
              <div className="range-header">
                <label className="form-label">Avg Comments / Post</label>
                <span className="range-value">{form.avg_comments.toLocaleString()}</span>
              </div>
              <input
                id="avg-comments-slider"
                type="range" min={0} max={50000} step={10}
                value={form.avg_comments}
                style={{ '--pct': `${pct(form.avg_comments, 0, 50000)}%` } as React.CSSProperties}
                onChange={e => update('avg_comments', Number(e.target.value))}
              />
            </div>
          </div>

          {/* Media Count */}
          <div className="range-group">
            <div className="range-header">
              <label className="form-label">Total Posts (Media Count)</label>
              <span className="range-value">{form.media_count.toLocaleString()}</span>
            </div>
            <input
              id="media-count-slider"
              type="range" min={1} max={10000} step={10}
              value={form.media_count}
              style={{ '--pct': `${pct(form.media_count, 1, 10000)}%` } as React.CSSProperties}
              onChange={e => update('media_count', Number(e.target.value))}
            />
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <div className="card-header">
          <span className="card-title">💰 Campaign Budget</span>
        </div>
        <div className="card-body">
          <div className="range-group">
            <div className="range-header">
              <label className="form-label">Campaign Spend (Rs.)</label>
              <span className="range-value">Rs. {form.spend.toLocaleString('en-IN')}</span>
            </div>
            <input
              id="spend-slider"
              type="range" min={500} max={100000} step={500}
              value={form.spend}
              style={{ '--pct': `${pct(form.spend, 500, 100000)}%` } as React.CSSProperties}
              onChange={e => update('spend', Number(e.target.value))}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)' }}>
              <span>Rs. 500</span><span>Rs. 10K</span><span>Rs. 50K</span><span>Rs. 100K</span>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="alert alert-error" style={{ marginTop: 16 }}>
          ⚠️ {error}
        </div>
      )}

      <div style={{ display: 'flex', gap: 12, marginTop: 20 }}>
        <button
          id="predict-btn"
          type="submit"
          className="btn btn-primary btn-lg"
          disabled={isPredicting}
          style={{ flex: 1 }}
        >
          {isPredicting ? (
            <><div className="spinner" style={{ width: 18, height: 18 }} /> Predicting…</>
          ) : (
            <><Zap size={18} /> Predict ROI</>
          )}
        </button>
        <button
          id="reset-btn"
          type="button"
          className="btn btn-secondary"
          onClick={handleReset}
        >
          <RefreshCw size={16} />
        </button>
      </div>
    </form>
  );
};

export default PredictionForm;
