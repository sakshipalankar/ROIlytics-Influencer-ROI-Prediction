import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import {
  X, CheckCircle, MapPin, Users, Heart, MessageCircle,
  TrendingUp, Bookmark, BookmarkCheck, BarChart2
} from 'lucide-react';
import { RadialBarChart, RadialBar, PolarAngleAxis, ResponsiveContainer } from 'recharts';

function fmtNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

const TIER_COLORS: Record<string, string> = {
  Nano: '#10b981', Micro: '#6366f1', Macro: '#f59e0b', Mega: '#f43f5e',
};

const InfluencerDetailModal: React.FC = () => {
  const { detailInfluencer, setDetailInfluencer, shortlist, addToShortlist, removeFromShortlist } = useAppStore();
  const inf = detailInfluencer;
  if (!inf) return null;

  const isInShortlist = shortlist.some(s => s.id === inf.id);
  const tierColor = TIER_COLORS[inf.follower_tier] ?? '#6366f1';

  const fitColor = inf.fit_score >= 75 ? '#10b981' : inf.fit_score >= 55 ? '#6366f1' : '#f59e0b';
  const gaugeData = [{ name: 'Fit', value: inf.fit_score }];

  return (
    <div className="modal-overlay" onClick={() => setDetailInfluencer(null)}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        {/* Close */}
        <button className="modal-close" onClick={() => setDetailInfluencer(null)}>
          <X size={18} />
        </button>

        {/* Header */}
        <div className="modal-header">
          <img
            src={inf.profile_pic_url}
            alt={inf.full_name}
            className="modal-avatar"
            onError={e => {
              (e.target as HTMLImageElement).src =
                `https://ui-avatars.com/api/?name=${encodeURIComponent(inf.full_name)}&size=96&background=6366f1&color=fff`;
            }}
          />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <h2 style={{ margin: 0, fontSize: 22, fontWeight: 900 }}>@{inf.username}</h2>
              {inf.is_verified && <CheckCircle size={18} color="#38bdf8" />}
            </div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 2 }}>{inf.full_name}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
              <MapPin size={13} color="var(--text-muted)" />
              <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>{inf.country}</span>
              <span className="inf-tag" style={{ marginLeft: 4, color: tierColor, borderColor: tierColor + '44', background: tierColor + '18' }}>
                {inf.follower_tier}
              </span>
              <span className="inf-tag">{inf.category}</span>
            </div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8, lineHeight: 1.6, maxWidth: 500 }}>
              {inf.biography}
            </p>
          </div>
        </div>

        {/* Stats row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12, margin: '20px 0' }}>
          {[
            { icon: <Users size={16}/>, label: 'Followers',   value: fmtNum(inf.followers_count), color: '#6366f1' },
            { icon: <Heart size={16}/>, label: 'Avg Likes',   value: fmtNum(inf.avg_likes),       color: '#f43f5e' },
            { icon: <MessageCircle size={16}/>, label: 'Avg Comments', value: fmtNum(inf.avg_comments), color: '#38bdf8' },
            { icon: <TrendingUp size={16}/>, label: 'Eng. Rate', value: `${(inf.engagement_rate*100).toFixed(2)}%`, color: '#10b981' },
            { icon: <BarChart2 size={16}/>, label: 'Posts/Week', value: `${inf.posting_frequency}x`, color: '#f59e0b' },
          ].map(s => (
            <div key={s.label} className="kpi-card" style={{ '--kpi-accent': s.color, padding: 12 } as React.CSSProperties}>
              <div style={{ color: s.color, marginBottom: 4 }}>{s.icon}</div>
              <div className="kpi-value" style={{ fontSize: 18 }}>{s.value}</div>
              <div className="kpi-label">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Fit Score + Audience */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
          {/* Fit Score gauge */}
          <div className="card" style={{ padding: 16 }}>
            <div className="card-title" style={{ marginBottom: 8 }}>🎯 Fit Score</div>
            <div style={{ position: 'relative', height: 140 }}>
              <ResponsiveContainer width="100%" height={140}>
                <RadialBarChart cx="50%" cy="80%" innerRadius="60%" outerRadius="100%"
                  startAngle={180} endAngle={0} data={gaugeData} barSize={16}>
                  <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
                  <RadialBar background={{ fill: 'rgba(255,255,255,0.04)' }}
                    dataKey="value" cornerRadius={8} fill={fitColor} angleAxisId={0} />
                </RadialBarChart>
              </ResponsiveContainer>
              <div style={{ position: 'absolute', bottom: 10, left: '50%', transform: 'translateX(-50%)', textAlign: 'center' }}>
                <div style={{ fontSize: 32, fontWeight: 900, color: fitColor, lineHeight: 1 }}>
                  {inf.fit_score.toFixed(0)}
                </div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>out of 100</div>
              </div>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', textAlign: 'center', marginTop: 4 }}>
              Pred. ROI: <strong style={{ color: '#10b981' }}>{inf.roi.toFixed(2)}x</strong>
            </div>
          </div>

          {/* Audience demographics */}
          <div className="card" style={{ padding: 16 }}>
            <div className="card-title" style={{ marginBottom: 12 }}>👥 Audience Split</div>
            <div style={{ marginBottom: 12 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                <span style={{ color: '#ec4899' }}>Female {Math.round(inf.audience_female_pct * 100)}%</span>
                <span style={{ color: '#38bdf8' }}>Male {Math.round(inf.audience_male_pct * 100)}%</span>
              </div>
              <div style={{ height: 8, borderRadius: 4, background: '#38bdf8', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${inf.audience_female_pct * 100}%`, background: '#ec4899', borderRadius: 4 }} />
              </div>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>Age distribution</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {[
                { label: '18–24', val: inf.audience_age_18_24 ?? 0.45, color: '#6366f1' },
                { label: '25–34', val: inf.audience_age_25_34 ?? 0.35, color: '#8b5cf6' },
                { label: '35–44', val: inf.audience_age_35_44 ?? 0.20, color: '#a78bfa' },
              ].map(a => (
                <div key={a.label}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 2 }}>
                    <span style={{ color: 'var(--text-secondary)' }}>{a.label}</span>
                    <span style={{ color: a.color, fontWeight: 700 }}>{Math.round((a.val ?? 0) * 100)}%</span>
                  </div>
                  <div style={{ height: 5, borderRadius: 3, background: 'rgba(255,255,255,0.05)' }}>
                    <div style={{ height: '100%', width: `${(a.val ?? 0) * 100}%`, background: a.color, borderRadius: 3 }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            className={`btn ${isInShortlist ? 'btn-secondary' : 'btn-primary'}`}
            style={{ flex: 1, height: 44 }}
            onClick={() => isInShortlist ? removeFromShortlist(inf.id) : addToShortlist(inf)}
          >
            {isInShortlist
              ? <><BookmarkCheck size={16} /> Remove from Shortlist</>
              : <><Bookmark size={16} /> Add to Shortlist</>
            }
          </button>
          <button className="btn btn-ghost" style={{ height: 44, padding: '0 20px' }}
            onClick={() => setDetailInfluencer(null)}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default InfluencerDetailModal;
