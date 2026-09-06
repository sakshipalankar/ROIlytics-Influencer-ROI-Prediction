import React, { useCallback } from 'react';
import { useAppStore } from '../store/useAppStore';
import { discoverInfluencers } from '../api/client';
import BrandSetupForm from '../components/discover/BrandSetupForm';
import InfluencerCardComponent from '../components/discover/InfluencerCard';
import InfluencerDetailModal from '../components/discover/InfluencerDetailModal';
import { TrendingUp, Sparkles } from 'lucide-react';

const Discover: React.FC = () => {
  const {
    brandProfile, discoveryResults, setDiscoveryResults,
    isDiscovering, setIsDiscovering, setDetailInfluencer,
    shortlist, setActivePage
  } = useAppStore();

  const handleSearch = useCallback(async () => {
    setIsDiscovering(true);
    setDiscoveryResults([]);
    try {
      const resp = await discoverInfluencers({ ...brandProfile, limit: 30 });
      setDiscoveryResults(resp.influencers);
    } catch (err) {
      console.error('Discovery failed:', err);
    } finally {
      setIsDiscovering(false);
    }
  }, [brandProfile]);

  return (
    <div className="animate-fade-in">
      {/* ─── Find Influencer Section: Shifted directly below Navigation Bar ─── */}
      <div className="find-influencer-header">
        <div className="fih-left">
          <div className="fih-badge">
            <Sparkles size={13} color="#a855f7" />
            <span>AI-Powered Influencer Discovery</span>
          </div>
          <h1 className="fih-title">
            Target High-Impact <span className="page-title-gradient">Influencers</span>
          </h1>
          <p className="fih-subtitle">
            Match and rank 10,500+ creator profiles using machine learning fit scoring, engagement analysis, and ROI prediction.
          </p>
        </div>

        <div className="fih-stats">
          <div className="fih-stat-item">
            <span className="fih-stat-val">10,500+</span>
            <span className="fih-stat-lbl">Real Profiles</span>
          </div>
          <div className="fih-stat-divider" />
          <div className="fih-stat-item">
            <span className="fih-stat-val">10</span>
            <span className="fih-stat-lbl">Categories</span>
          </div>
          <div className="fih-stat-divider" />
          <div className="fih-stat-item">
            <span className="fih-stat-val">ML Fit</span>
            <span className="fih-stat-lbl">Smart Ranking</span>
          </div>
          <div className="fih-stat-divider" />
          <div className="fih-stat-item">
            <span className="fih-stat-val">17</span>
            <span className="fih-stat-lbl">Countries</span>
          </div>
        </div>
      </div>

      {/* ─── Brand Setup Master Card (Full Dashboard Hub) ─── */}
      <div className="card bsh-master-card">
        <div className="card-header bsh-master-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className="card-title" style={{ fontSize: 15, fontWeight: 800 }}>🎯 Brand Setup & Campaign Targeting</span>
          </div>
          <span className="badge badge-indigo" style={{ fontSize: 11, padding: '3px 10px' }}>
            {brandProfile.category} · Rs. {brandProfile.budget.toLocaleString('en-IN')} · {brandProfile.goal}
          </span>
        </div>
        <div className="card-body" style={{ padding: '20px 22px' }}>
          <BrandSetupForm onSearch={handleSearch} />
        </div>
      </div>

      {/* ─── Results Section (Appears when searching or results exist) ─── */}
      {(isDiscovering || discoveryResults.length > 0) && (
        <main className="discover-results" style={{ marginTop: 24 }}>
          {/* Loading */}
          {isDiscovering && (
            <div className="card" style={{ textAlign: 'center', padding: '60px 24px' }}>
              <div className="spinner" style={{ width: 40, height: 40, margin: '0 auto 16px' }} />
              <div style={{ fontWeight: 700, fontSize: 16 }}>Finding your best influencers…</div>
              <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 8 }}>
                Scoring {brandProfile.category} influencers against your brand profile & campaign goal
              </p>
            </div>
          )}

          {/* Results */}
          {!isDiscovering && discoveryResults.length > 0 && (
            <>
              {/* Results header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <div>
                  <span style={{ fontWeight: 800, fontSize: 20 }}>
                    Top {discoveryResults.length} {brandProfile.category} Influencers
                  </span>
                  <span style={{ fontSize: 13, color: 'var(--text-muted)', marginLeft: 10 }}>
                    for {brandProfile.brand_name || 'your brand'} · Rs. {brandProfile.budget.toLocaleString('en-IN')} budget
                  </span>
                </div>
                {shortlist.length > 0 && (
                  <button
                    className="btn btn-secondary btn-sm"
                    onClick={() => setActivePage('shortlist')}
                  >
                    View Shortlist ({shortlist.length})
                  </button>
                )}
              </div>

              {/* Top 3 highlight */}
              <div className="top3-banner">
                <TrendingUp size={16} style={{ color: '#f59e0b' }} />
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                  Ranked by <strong>Fit Score</strong> — combining engagement rate, follower tier, predicted ROI, and campaign goal alignment
                </span>
              </div>

              {/* Card grid */}
              <div className="influencer-grid">
                {discoveryResults.map((inf, idx) => (
                  <div key={inf.id} style={{ position: 'relative' }}>
                    {idx < 3 && (
                      <div className="rank-badge">#{idx + 1}</div>
                    )}
                    <InfluencerCardComponent
                      influencer={inf}
                      onViewDetail={setDetailInfluencer}
                    />
                  </div>
                ))}
              </div>
            </>
          )}
        </main>
      )}

      {/* Detail Modal */}
      <InfluencerDetailModal />
    </div>
  );
};

export default Discover;
