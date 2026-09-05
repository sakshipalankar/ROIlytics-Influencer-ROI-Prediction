import React, { useEffect, useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { getAnalyticsOverview } from '../api/client';
import type { CreatorProfile } from '../types';
import { Database, Search } from 'lucide-react';
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ZAxis
} from 'recharts';

const TIER_COLOR: Record<string, string> = {
  Nano: '#10b981', Micro: '#6366f1', Macro: '#f59e0b', Mega: '#f43f5e'
};

function getBucket(f: number) {
  if (f < 10000) return 'Nano';
  if (f < 100000) return 'Micro';
  if (f < 1000000) return 'Macro';
  return 'Mega';
}

const Explorer: React.FC = () => {
  const { overview, setOverview } = useAppStore();
  const [search, setSearch] = useState('');
  const [catFilter, setCatFilter] = useState('All');
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 8;

  useEffect(() => {
    if (!overview) getAnalyticsOverview().then(setOverview).catch(console.error);
  }, []);

  const profiles: CreatorProfile[] = overview?.profiles ?? [];
  const categories = ['All', ...Array.from(new Set(profiles.map(p => p.category)))];

  const filtered = profiles.filter(p =>
    (catFilter === 'All' || p.category === catFilter) &&
    (search === '' || p.name.toLowerCase().includes(search.toLowerCase()))
  );

  const pageCount = Math.ceil(filtered.length / PAGE_SIZE);
  const paged = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const scatterData = profiles.map(p => ({
    x: p.followers_count,
    y: p.avg_likes > 0 ? ((p.avg_likes + p.avg_comments) / p.followers_count) * 100 : 0,
    name: p.name,
    tier: getBucket(p.followers_count),
  }));

  const handleExport = () => {
    const headers = ['name', 'category', 'followers_count', 'media_count', 'avg_likes', 'avg_comments', 'posting_frequency'];
    const rows = filtered.map(p => headers.map(h => (p as any)[h]).join(','));
    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'creator_profiles.csv';
    a.click();
  };

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1 className="page-title">
          <Database size={28} />
          <span className="page-title-gradient">Data Explorer</span>
        </h1>
        <p className="page-subtitle">Browse and filter the influencer profile dataset used for training.</p>
      </div>

      {/* Scatter plot */}
      {scatterData.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header">
            <span className="card-title">📡 Followers vs Engagement Rate</span>
          </div>
          <div className="card-body">
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={260}>
                <ScatterChart margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis
                    type="number" dataKey="x" name="Followers"
                    tickFormatter={v => v >= 1000000 ? `${(v / 1000000).toFixed(1)}M` : `${(v / 1000).toFixed(0)}K`}
                    tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false}
                  />
                  <YAxis
                    type="number" dataKey="y" name="Engagement %"
                    tickFormatter={v => `${v.toFixed(1)}%`}
                    tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} width={50}
                  />
                  <ZAxis range={[40, 200]} />
                  <Tooltip
                    contentStyle={{ background: '#0d1220', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 10, fontSize: 12, color: '#f1f5f9' }}
                    cursor={{ fill: 'rgba(99,102,241,0.05)' }}
                    content={({ payload }) => {
                      if (!payload?.length) return null;
                      const d = payload[0].payload;
                      return (
                        <div style={{ padding: '10px 14px', background: '#0d1220', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 10 }}>
                          <div style={{ fontWeight: 700, color: '#f1f5f9' }}>{d.name}</div>
                          <div style={{ color: '#94a3b8', fontSize: 12 }}>Followers: {d.x.toLocaleString()}</div>
                          <div style={{ color: '#94a3b8', fontSize: 12 }}>Engagement: {d.y.toFixed(2)}%</div>
                          <div style={{ color: TIER_COLOR[d.tier], fontSize: 11, marginTop: 4 }}>{d.tier}</div>
                        </div>
                      );
                    }}
                  />
                  <Scatter
                    data={scatterData}
                    fill="#6366f1"
                    shape={(props: any) => {
                      const color = TIER_COLOR[props.payload.tier] ?? '#6366f1';
                      return <circle cx={props.cx} cy={props.cy} r={6} fill={color} fillOpacity={0.8} stroke={color} strokeWidth={1.5} />;
                    }}
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
            <div style={{ display: 'flex', gap: 16, marginTop: 12, flexWrap: 'wrap' }}>
              {Object.entries(TIER_COLOR).map(([tier, color]) => (
                <span key={tier} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#94a3b8' }}>
                  <span style={{ width: 10, height: 10, borderRadius: '50%', background: color, display: 'inline-block' }} />
                  {tier}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Filters & Table */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">👥 Creator Profiles ({filtered.length})</span>
          <button id="export-btn" className="btn btn-secondary btn-sm" onClick={handleExport}>
            Export CSV
          </button>
        </div>
        <div className="card-body">
          <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
            <div style={{ position: 'relative', flex: 1, minWidth: 200 }}>
              <Search size={14} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                id="profile-search"
                className="form-input"
                style={{ paddingLeft: 34 }}
                placeholder="Search by name…"
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(0); }}
              />
            </div>
            <select
              id="category-filter"
              className="form-select"
              style={{ width: 160 }}
              value={catFilter}
              onChange={e => { setCatFilter(e.target.value); setPage(0); }}
            >
              {categories.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          {profiles.length === 0 ? (
            <div className="loader-overlay">
              <div className="spinner" /> Loading profiles…
            </div>
          ) : (
            <>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Creator</th>
                    <th>Category</th>
                    <th>Followers</th>
                    <th>Avg Likes</th>
                    <th>Avg Comments</th>
                    <th>ER</th>
                    <th>Posts/Wk</th>
                    <th>Tier</th>
                  </tr>
                </thead>
                <tbody>
                  {paged.map(p => {
                    const er = p.followers_count > 0
                      ? ((p.avg_likes + p.avg_comments) / p.followers_count * 100).toFixed(2)
                      : '—';
                    const tier = getBucket(p.followers_count);
                    return (
                      <tr key={p.name}>
                        <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{p.name}</td>
                        <td><span className="badge badge-indigo">{p.category}</span></td>
                        <td className="font-mono">{p.followers_count.toLocaleString()}</td>
                        <td className="font-mono">{p.avg_likes.toLocaleString()}</td>
                        <td className="font-mono">{p.avg_comments.toLocaleString()}</td>
                        <td className="font-mono" style={{ color: 'var(--accent-emerald)' }}>{er}%</td>
                        <td className="font-mono">{p.posting_frequency}</td>
                        <td>
                          <span style={{ color: TIER_COLOR[tier], fontSize: 12, fontWeight: 700 }}>{tier}</span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {pageCount > 1 && (
                <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 16 }}>
                  <button
                    className="btn btn-ghost btn-sm"
                    disabled={page === 0}
                    onClick={() => setPage(p => p - 1)}
                  >← Prev</button>
                  <span style={{ padding: '6px 12px', fontSize: 13, color: 'var(--text-secondary)' }}>
                    Page {page + 1} / {pageCount}
                  </span>
                  <button
                    className="btn btn-ghost btn-sm"
                    disabled={page >= pageCount - 1}
                    onClick={() => setPage(p => p + 1)}
                  >Next →</button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Explorer;
