import React from 'react';
import type { InfluencerCard } from '../../types';
import { useAppStore } from '../../store/useAppStore';
import { Bookmark, BookmarkCheck, ChevronRight, MapPin, CheckCircle } from 'lucide-react';

const TIER_COLORS: Record<string, string> = {
  Nano:  '#10b981',
  Micro: '#6366f1',
  Macro: '#f59e0b',
  Mega:  '#f43f5e',
};

function fitBadgeColor(score: number): string {
  if (score >= 75) return '#10b981';
  if (score >= 55) return '#6366f1';
  if (score >= 35) return '#f59e0b';
  return '#f43f5e';
}

function fmtNum(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(0)}K`;
  return String(n);
}

interface Props {
  influencer: InfluencerCard;
  onViewDetail: (inf: InfluencerCard) => void;
}

const InfluencerCardComponent: React.FC<Props> = ({ influencer: inf, onViewDetail }) => {
  const { shortlist, addToShortlist, removeFromShortlist } = useAppStore();
  const isInShortlist = shortlist.some(s => s.id === inf.id);
  const tierColor = TIER_COLORS[inf.follower_tier] ?? '#6366f1';
  const fitColor  = fitBadgeColor(inf.fit_score);

  const handleShortlist = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (isInShortlist) removeFromShortlist(inf.id);
    else addToShortlist(inf);
  };

  return (
    <div
      className="influencer-card"
      onClick={() => onViewDetail(inf)}
      role="button"
      tabIndex={0}
      onKeyDown={e => e.key === 'Enter' && onViewDetail(inf)}
    >
      {/* Header */}
      <div className="inf-card-header">
        <img
          src={inf.profile_pic_url}
          alt={inf.full_name}
          className="inf-avatar"
          onError={e => {
            (e.target as HTMLImageElement).src =
              `https://ui-avatars.com/api/?name=${encodeURIComponent(inf.full_name)}&size=80&background=6366f1&color=fff`;
          }}
        />
        <div className="inf-card-meta">
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span className="inf-name">@{inf.username}</span>
            {inf.is_verified && (
              <CheckCircle size={13} style={{ color: '#38bdf8', flexShrink: 0 }} />
            )}
          </div>
          <div className="inf-fullname">{inf.full_name}</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
            <MapPin size={11} style={{ color: 'var(--text-muted)' }} />
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{inf.country}</span>
          </div>
        </div>
        <button
          className={`shortlist-btn${isInShortlist ? ' active' : ''}`}
          onClick={handleShortlist}
          title={isInShortlist ? 'Remove from shortlist' : 'Add to shortlist'}
        >
          {isInShortlist
            ? <BookmarkCheck size={16} />
            : <Bookmark size={16} />
          }
        </button>
      </div>

      {/* Tags */}
      <div style={{ display: 'flex', gap: 6, margin: '10px 0 8px' }}>
        <span className="inf-tag" style={{ color: tierColor, borderColor: tierColor + '44', background: tierColor + '15' }}>
          {inf.follower_tier}
        </span>
        <span className="inf-tag">{inf.category}</span>
        <span className="inf-tag" style={{ fontSize: 10 }}>{inf.sub_category}</span>
      </div>

      {/* Bio */}
      <p className="inf-bio">{inf.biography}</p>

      {/* Stats grid */}
      <div className="inf-stats-grid">
        <div className="inf-stat">
          <span className="inf-stat-value">{fmtNum(inf.followers_count)}</span>
          <span className="inf-stat-label">Followers</span>
        </div>
        <div className="inf-stat">
          <span className="inf-stat-value" style={{ color: '#10b981' }}>
            {(inf.engagement_rate * 100).toFixed(2)}%
          </span>
          <span className="inf-stat-label">Eng. Rate</span>
        </div>
        <div className="inf-stat">
          <span className="inf-stat-value">{fmtNum(inf.avg_likes)}</span>
          <span className="inf-stat-label">Avg Likes</span>
        </div>
        <div className="inf-stat">
          <span className="inf-stat-value">{fmtNum(inf.avg_comments)}</span>
          <span className="inf-stat-label">Avg Comments</span>
        </div>
      </div>

      {/* Fit Score + ROI */}
      <div className="inf-score-row">
        <div className="inf-score-item">
          <div
            className="inf-fit-score"
            style={{ color: fitColor, borderColor: fitColor + '55', background: fitColor + '18' }}
          >
            <span style={{ fontSize: 18, fontWeight: 900 }}>{inf.fit_score.toFixed(0)}</span>
            <span style={{ fontSize: 11, fontWeight: 600 }}>/100</span>
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 3, textAlign: 'center' }}>Fit Score</div>
        </div>
        <div className="inf-score-item">
          <div className="inf-roi-badge">
            <span style={{ fontSize: 18, fontWeight: 900, color: inf.roi >= 1.5 ? '#10b981' : inf.roi >= 0.5 ? '#f59e0b' : '#f43f5e' }}>
              {inf.roi.toFixed(2)}x
            </span>
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 3, textAlign: 'center' }}>Pred. ROI</div>
        </div>
      </div>

      {/* Footer CTA */}
      <div className="inf-card-footer">
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
          {inf.posting_frequency}x/wk · {fmtNum(inf.estimated_reach)} reach
        </span>
        <span style={{ fontSize: 12, color: 'var(--accent-primary)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 2 }}>
          View <ChevronRight size={14} />
        </span>
      </div>
    </div>
  );
};

export default InfluencerCardComponent;
