import React from 'react';
import type { PredictResponse } from '../../types';

interface Props {
  result: PredictResponse;
}

const fmt = (n: number, decimals = 2) =>
  n.toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });

const fmtUSD = (n: number) =>
  n.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });

const KPI_DEFS = (r: PredictResponse) => [
  {
    label: 'Predicted ROI',
    value: `${fmt(r.roi)}x`,
    sub: r.tier,
    accent: r.tier_color,
  },
  {
    label: 'Predicted Revenue',
    value: fmtUSD(r.predicted_revenue),
    sub: 'Gross return on campaign',
    accent: '#10b981',
  },
  {
    label: 'Predicted Profit',
    value: fmtUSD(r.predicted_profit),
    sub: r.predicted_profit >= 0 ? 'Net positive' : 'Net loss',
    accent: r.predicted_profit >= 0 ? '#10b981' : '#f43f5e',
  },
  {
    label: 'Engagement Rate',
    value: `${(r.engagement_rate * 100).toFixed(2)}%`,
    sub: `${r.follower_tier} influencer`,
    accent: '#38bdf8',
  },
];

const ResultKpiCards: React.FC<Props> = ({ result }) => {
  const kpis = KPI_DEFS(result);
  return (
    <div className="kpi-grid animate-fade-up">
      {kpis.map((kpi, i) => (
        <div
          key={kpi.label}
          className="kpi-card"
          style={{
            animationDelay: `${i * 60}ms`,
            animationFillMode: 'both',
            // @ts-ignore
            '--kpi-accent': kpi.accent,
          }}
        >
          <div className="kpi-label">{kpi.label}</div>
          <div className="kpi-value">{kpi.value}</div>
          <div className="kpi-sub">{kpi.sub}</div>
        </div>
      ))}
      {/* Tier pill */}
      <div className="col-span-2" style={{ gridColumn: '1 / -1', marginTop: 4 }}>
        <div
          className="tier-pill"
          style={{
            color: result.tier_color,
            borderColor: result.tier_color + '55',
            background: result.tier_color + '18',
            fontSize: 13,
          }}
        >
          <span style={{ fontSize: 16 }}>
            {result.roi >= 3 ? '🚀' : result.roi >= 2 ? '⭐' : result.roi >= 1 ? '✅' : result.roi >= 0 ? '⚠️' : '❌'}
          </span>
          {result.tier} ROI — {result.follower_tier} Influencer Tier
        </div>
      </div>
    </div>
  );
};

export default ResultKpiCards;
