import React, { useState } from 'react';
import { fetchInstagramProfile } from '../../api/client';
import { predictSingle } from '../../api/client';
import { useAppStore } from '../../store/useAppStore';
import type { InstagramProfile } from '../../types';
import { Search, Zap } from 'lucide-react';

const LiveApiPanel: React.FC = () => {
  const { setPredictionResult } = useAppStore();
  const [token, setToken] = useState('');
  const [username, setUsername] = useState('');
  const [profile, setProfile] = useState<InstagramProfile | null>(null);
  const [spend, setSpend] = useState(5000);
  const [loading, setLoading] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFetch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !token) return;
    setLoading(true);
    setError(null);
    setProfile(null);
    try {
      const data = await fetchInstagramProfile(username, token);
      setProfile(data);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Failed to fetch profile');
    } finally {
      setLoading(false);
    }
  };

  const handlePredict = async () => {
    if (!profile) return;
    setPredicting(true);
    try {
      const result = await predictSingle({
        followers_count: profile.followers_count,
        media_count: profile.media_count,
        avg_likes: profile.avg_likes,
        avg_comments: profile.avg_comments,
        category: 'Lifestyle',
        posting_frequency: 4,
        spend,
      });
      setPredictionResult(result);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? 'Prediction failed');
    } finally {
      setPredicting(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div className="alert alert-warn" style={{ fontSize: 13 }}>
        <span>⚠️</span>
        <div>
          <strong>Instagram Business Discovery API</strong><br />
          Only works for Business or Creator accounts. You need a valid Facebook User Access Token
          with <code>pages_read_engagement</code> and <code>instagram_manage_insights</code> permissions.
        </div>
      </div>

      <form onSubmit={handleFetch} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div className="form-group">
          <label className="form-label">Instagram Username</label>
          <input
            id="ig-username-input"
            type="text"
            className="form-input"
            placeholder="e.g. cristiano"
            value={username}
            onChange={e => setUsername(e.target.value)}
          />
        </div>
        <div className="form-group">
          <label className="form-label">Facebook User Access Token</label>
          <input
            id="ig-token-input"
            type="password"
            className="form-input"
            placeholder="EAAxxxxxxx..."
            value={token}
            onChange={e => setToken(e.target.value)}
          />
        </div>
        <button
          id="ig-fetch-btn"
          type="submit"
          className="btn btn-primary"
          disabled={loading || !username || !token}
        >
          {loading ? (
            <><div className="spinner" style={{ width: 16, height: 16 }} /> Fetching…</>
          ) : (
            <><Search size={16} /> Fetch Profile</>
          )}
        </button>
      </form>

      {error && <div className="alert alert-error">⚠️ {error}</div>}

      {profile && (
        <div className="card card-gradient animate-scale-in">
          <div className="card-body">
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
              {profile.profile_picture_url && (
                <img
                  src={profile.profile_picture_url}
                  alt={profile.username}
                  style={{ width: 56, height: 56, borderRadius: '50%', border: '2px solid var(--accent-primary)' }}
                />
              )}
              <div>
                <div style={{ fontWeight: 800, fontSize: 18 }}>@{profile.username}</div>
                {profile.biography && (
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2, maxWidth: 360 }}>
                    {profile.biography}
                  </div>
                )}
              </div>
            </div>
            <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
              <div className="kpi-card" style={{ padding: 14, '--kpi-accent': '#6366f1' } as React.CSSProperties}>
                <div className="kpi-label">Followers</div>
                <div className="kpi-value" style={{ fontSize: 20 }}>{profile.followers_count.toLocaleString()}</div>
              </div>
              <div className="kpi-card" style={{ padding: 14, '--kpi-accent': '#10b981' } as React.CSSProperties}>
                <div className="kpi-label">Avg Likes</div>
                <div className="kpi-value" style={{ fontSize: 20 }}>{profile.avg_likes.toLocaleString()}</div>
              </div>
              <div className="kpi-card" style={{ padding: 14, '--kpi-accent': '#38bdf8' } as React.CSSProperties}>
                <div className="kpi-label">Avg Comments</div>
                <div className="kpi-value" style={{ fontSize: 20 }}>{profile.avg_comments.toLocaleString()}</div>
              </div>
            </div>

            <div style={{ marginTop: 16 }}>
              <div className="range-group">
                <div className="range-header">
                  <label className="form-label">Campaign Spend for Prediction</label>
                  <span className="range-value">Rs. {spend.toLocaleString('en-IN')}</span>
                </div>
                <input
                  type="range" min={500} max={100000} step={500}
                  value={spend}
                  style={{ '--pct': `${Math.round(((spend - 500) / 99500) * 100)}%` } as React.CSSProperties}
                  onChange={e => setSpend(Number(e.target.value))}
                />
              </div>
            </div>

            <button
              id="ig-predict-btn"
              className="btn btn-primary"
              style={{ width: '100%', marginTop: 16 }}
              onClick={handlePredict}
              disabled={predicting}
            >
              {predicting ? (
                <><div className="spinner" style={{ width: 16, height: 16 }} /> Predicting…</>
              ) : (
                <><Zap size={16} /> Predict ROI for @{profile.username}</>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default LiveApiPanel;
