import React from 'react';
import { useAppStore } from '../store/useAppStore';
import { Bookmark, X, Download, ArrowRight } from 'lucide-react';

function fmtNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

const Shortlist: React.FC = () => {
  const { shortlist, removeFromShortlist, clearShortlist, brandProfile, setActivePage } = useAppStore();

  const handleExport = () => {
    const headers = [
      'Username','Full Name','Category','Followers','Engagement Rate',
      'Avg Likes','Avg Comments','Fit Score','Predicted ROI','Country','Tier'
    ];
    const rows = shortlist.map(inf => [
      inf.username, inf.full_name, inf.category,
      inf.followers_count, (inf.engagement_rate * 100).toFixed(2) + '%',
      inf.avg_likes, inf.avg_comments, inf.fit_score, inf.roi.toFixed(2) + 'x',
      inf.country, inf.follower_tier,
    ]);
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `shortlist_${brandProfile.brand_name || 'brand'}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (shortlist.length === 0) {
    return (
      <div className="animate-fade-in">
        <div className="page-header">
          <h1 className="page-title">
            <Bookmark size={28} />
            <span className="page-title-gradient">My Shortlist</span>
          </h1>
          <p className="page-subtitle">Save and compare your top influencer picks.</p>
        </div>
        <div className="card" style={{ textAlign: 'center', padding: '80px 24px' }}>
          <div style={{ fontSize: 56, marginBottom: 16 }}>📋</div>
          <div style={{ fontWeight: 800, fontSize: 20, marginBottom: 8 }}>Your shortlist is empty</div>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 24 }}>
            Go to Discover, browse influencers, and click the bookmark icon to add up to 5 to your shortlist.
          </p>
          <button className="btn btn-primary" onClick={() => setActivePage('discover')}>
            <ArrowRight size={16} /> Go to Discover
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1 className="page-title">
          <Bookmark size={28} />
          <span className="page-title-gradient">My Shortlist</span>
        </h1>
        <p className="page-subtitle">
          Compare your top {shortlist.length} influencer picks side-by-side.
        </p>
      </div>

      {/* Actions bar */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <button className="btn btn-primary" onClick={handleExport}>
          <Download size={15} /> Export CSV
        </button>
        <button className="btn btn-ghost" onClick={clearShortlist}>
          <X size={15} /> Clear All
        </button>
        <button className="btn btn-secondary" onClick={() => setActivePage('discover')}>
          + Add More
        </button>
      </div>

      {/* Comparison table */}
      <div className="card">
        <div className="card-body" style={{ overflowX: 'auto' }}>
          <table className="data-table compare-table">
            <thead>
              <tr>
                <th style={{ width: 140 }}>Metric</th>
                {shortlist.map(inf => (
                  <th key={inf.id}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                      <img
                        src={inf.profile_pic_url}
                        alt={inf.username}
                        style={{ width: 44, height: 44, borderRadius: '50%', border: '2px solid var(--accent-primary)' }}
                        onError={e => {
                          (e.target as HTMLImageElement).src =
                            `https://ui-avatars.com/api/?name=${encodeURIComponent(inf.full_name)}&size=44&background=6366f1&color=fff`;
                        }}
                      />
                      <div style={{ fontSize: 12, fontWeight: 700 }}>@{inf.username}</div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>{inf.category}</div>
                      <button
                        className="btn btn-ghost btn-sm"
                        style={{ padding: '2px 6px', fontSize: 10 }}
                        onClick={() => removeFromShortlist(inf.id)}
                      >
                        <X size={10} /> Remove
                      </button>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[
                {
                  label: '🎯 Fit Score',
                  key: 'fit_score',
                  fmt: (v: number) => (
                    <span style={{
                      fontWeight: 900, fontSize: 16,
                      color: v >= 75 ? '#10b981' : v >= 55 ? '#6366f1' : '#f59e0b'
                    }}>{v.toFixed(0)}/100</span>
                  ),
                  best: (vals: number[]) => vals.indexOf(Math.max(...vals)),
                },
                {
                  label: '💰 Pred. ROI',
                  key: 'roi',
                  fmt: (v: number) => <span style={{ fontWeight: 700, color: v >= 1.5 ? '#10b981' : '#f59e0b' }}>{v.toFixed(2)}x</span>,
                  best: (vals: number[]) => vals.indexOf(Math.max(...vals)),
                },
                {
                  label: '👥 Followers',
                  key: 'followers_count',
                  fmt: (v: number) => fmtNum(v),
                  best: (vals: number[]) => vals.indexOf(Math.max(...vals)),
                },
                {
                  label: '❤️ Eng. Rate',
                  key: 'engagement_rate',
                  fmt: (v: number) => `${(v * 100).toFixed(2)}%`,
                  best: (vals: number[]) => vals.indexOf(Math.max(...vals)),
                },
                {
                  label: '👍 Avg Likes',
                  key: 'avg_likes',
                  fmt: (v: number) => fmtNum(v),
                  best: (vals: number[]) => vals.indexOf(Math.max(...vals)),
                },
                {
                  label: '💬 Avg Comments',
                  key: 'avg_comments',
                  fmt: (v: number) => fmtNum(v),
                  best: (vals: number[]) => vals.indexOf(Math.max(...vals)),
                },
                {
                  label: '📡 Est. Reach',
                  key: 'estimated_reach',
                  fmt: (v: number) => fmtNum(v),
                  best: (vals: number[]) => vals.indexOf(Math.max(...vals)),
                },
                {
                  label: '📅 Posts/Week',
                  key: 'posting_frequency',
                  fmt: (v: number) => `${v}x`,
                  best: (vals: number[]) => vals.indexOf(Math.max(...vals)),
                },
                {
                  label: '🌍 Country',
                  key: 'country',
                  fmt: (v: string) => v,
                  best: () => -1,
                },
                {
                  label: '👤 Tier',
                  key: 'follower_tier',
                  fmt: (v: string) => v,
                  best: () => -1,
                },
              ].map(row => {
                const vals = shortlist.map(inf => (inf as any)[row.key]);
                const numVals = vals.every(v => typeof v === 'number') ? (vals as number[]) : null;
                const bestIdx = numVals ? row.best(numVals) : -1;
                return (
                  <tr key={row.label}>
                    <td style={{ fontWeight: 600, color: 'var(--text-secondary)', fontSize: 13 }}>{row.label}</td>
                    {shortlist.map((inf, i) => (
                      <td
                        key={inf.id}
                        style={{
                          textAlign: 'center',
                          background: i === bestIdx ? 'rgba(99,102,241,0.08)' : undefined,
                          fontWeight: i === bestIdx ? 700 : 400,
                        }}
                      >
                        {(row.fmt as Function)((inf as any)[row.key])}
                        {i === bestIdx && numVals && (
                          <span style={{ fontSize: 10, color: '#10b981', display: 'block' }}>Best ⭐</span>
                        )}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Visual fit score comparison */}
      <div className="card" style={{ marginTop: 20 }}>
        <div className="card-header">
          <span className="card-title">🏆 Fit Score Comparison</span>
        </div>
        <div className="card-body">
          {shortlist.map(inf => (
            <div key={inf.id} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
              <img
                src={inf.profile_pic_url}
                alt={inf.username}
                style={{ width: 32, height: 32, borderRadius: '50%', flexShrink: 0 }}
                onError={e => {
                  (e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${encodeURIComponent(inf.full_name)}&size=32&background=6366f1&color=fff`;
                }}
              />
              <div style={{ fontSize: 13, fontWeight: 600, width: 120, flexShrink: 0 }}>@{inf.username}</div>
              <div style={{ flex: 1, height: 10, borderRadius: 5, background: 'rgba(255,255,255,0.05)', overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${inf.fit_score}%`,
                  borderRadius: 5,
                  background: inf.fit_score >= 75 ? '#10b981' : inf.fit_score >= 55 ? '#6366f1' : '#f59e0b',
                  transition: 'width 0.8s ease',
                }} />
              </div>
              <div style={{ fontSize: 14, fontWeight: 800, width: 50, textAlign: 'right',
                color: inf.fit_score >= 75 ? '#10b981' : inf.fit_score >= 55 ? '#6366f1' : '#f59e0b' }}>
                {inf.fit_score.toFixed(0)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Shortlist;
