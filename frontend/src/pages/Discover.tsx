import React, { useCallback } from 'react';
import { useAppStore } from '../store/useAppStore';
import { discoverInfluencers } from '../api/client';
import BrandSetupForm from '../components/discover/BrandSetupForm';
import InfluencerCardComponent from '../components/discover/InfluencerCard';
import InfluencerDetailModal from '../components/discover/InfluencerDetailModal';
import { TrendingUp } from 'lucide-react';

const Discover: React.FC = () => {
  const {
    brandProfile, discoveryResults, setDiscoveryResults,
    unreliableResults, setUnreliableResults,
    discoveryNotice, setDiscoveryNotice,
    isDiscovering, setIsDiscovering, setDetailInfluencer,
    shortlist, setActivePage
  } = useAppStore();

  const [searchError, setSearchError] = React.useState<string | null>(null);
  const [hasSearched, setHasSearched] = React.useState(false);

  const handleSearch = useCallback(async () => {
    setIsDiscovering(true);
    setSearchError(null);
    setHasSearched(true);
    setDiscoveryResults([]);
    setUnreliableResults([]);
    setDiscoveryNotice(null);
    try {
      const resp = await discoverInfluencers({ ...brandProfile, limit: 30 });
      setDiscoveryResults(resp.influencers || []);
      setUnreliableResults(resp.unreliable_influencers || []);
      setDiscoveryNotice(resp.notice || null);
    } catch (err: any) {
      console.error('Discovery failed:', err);
      setSearchError(err?.response?.data?.detail || err?.message || 'Failed to score influencers.');
    } finally {
      setIsDiscovering(false);
    }
  }, [brandProfile]);

  return (
    <div className="animate-fade-in">
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

      {/* Error alert */}
      {searchError && (
        <div className="auth-alert auth-alert-error" style={{ marginTop: 16 }}>
          <span>⚠️ {searchError}</span>
        </div>
      )}

      {/* Empty results after search */}
      {hasSearched && !isDiscovering && !searchError && discoveryResults.length === 0 && unreliableResults.length === 0 && (
        <div className="card" style={{ textAlign: 'center', padding: '48px 24px', marginTop: 24 }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>🔍</div>
          <h3 style={{ fontSize: 17, fontWeight: 700, marginBottom: 6 }}>No Influencers Matched All Filters</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: 13, maxWidth: 440, margin: '0 auto 16px' }}>
            Try adjusting your search criteria or adding more influencers to the database.
          </p>
          <button className="btn btn-primary btn-sm" onClick={handleSearch}>
            Refresh Results
          </button>
        </div>
      )}

      {/* ─── Results Section (Appears when searching or results exist) ─── */}
      {(isDiscovering || discoveryResults.length > 0 || unreliableResults.length > 0) && (
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

              {discoveryNotice && (
                <div className="auth-alert auth-alert-error" style={{ marginTop: 16, marginBottom: 16 }}>
                  <span>⚠️ {discoveryNotice}</span>
                </div>
              )}

              {/* Top 3 highlight */}
              <div className="top3-banner">
                <TrendingUp size={16} style={{ color: '#f59e0b' }} />
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                  Ranked by <strong>Fit Score</strong> — combining engagement rate, predicted ROI, and campaign goal alignment
                </span>
              </div>

              {/* Card grid */}
              <div className="influencer-grid">
                {discoveryResults.map((inf, idx) => (
                  <div key={inf.id || inf.username} style={{ position: 'relative' }}>
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

          {/* Unreliable Results */}
          {!isDiscovering && unreliableResults.length > 0 && (
            <div style={{ marginTop: 40 }}>
              <div style={{ marginBottom: 16 }}>
                <span style={{ fontWeight: 800, fontSize: 20, color: 'var(--text-secondary)' }}>
                  Not Enough Data ({unreliableResults.length})
                </span>
                <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                  These profiles are missing data or have too few followers/posts for reliable ROI prediction.
                </p>
              </div>
              <div className="influencer-grid" style={{ opacity: 0.7 }}>
                {unreliableResults.map((inf) => (
                  <div key={inf.id || inf.username}>
                    <InfluencerCardComponent
                      influencer={inf}
                      onViewDetail={setDetailInfluencer}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      )}

      {/* Detail Modal */}
      <InfluencerDetailModal />
    </div>
  );
};

export default Discover;
