import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import type { FeatureImportance } from '../../types';

interface Props {
  features: FeatureImportance[];
}

const FEATURE_LABELS: Record<string, string> = {
  log_followers: 'Log Followers',
  followers_count: 'Followers Count',
  engagement_rate: 'Engagement Rate',
  spend: 'Campaign Spend',
  avg_likes: 'Avg Likes',
  avg_comments: 'Avg Comments',
  posting_frequency: 'Posting Frequency',
  follower_bucket_encoded: 'Follower Tier',
  category_encoded: 'Category',
  media_count: 'Media Count',
  likes_to_comments_ratio: 'Likes/Comments Ratio',
};

const FeatureImportanceChart: React.FC<Props> = ({ features }) => {
  const sorted = [...features].sort((a, b) => b.importance - a.importance).slice(0, 10);
  const max = sorted[0]?.importance ?? 1;

  return (
    <div className="chart-container">
      <ResponsiveContainer width="100%" height={Math.max(280, sorted.length * 34)}>
        <BarChart
          data={sorted}
          layout="vertical"
          margin={{ top: 0, right: 20, left: 140, bottom: 0 }}
          barCategoryGap="20%"
        >
          <XAxis
            type="number"
            domain={[0, max * 1.1]}
            tickFormatter={v => `${(v * 100).toFixed(1)}%`}
            tick={{ fill: '#64748b', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="feature"
            tickFormatter={f => FEATURE_LABELS[f] ?? f}
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            width={135}
          />
          <Tooltip
            contentStyle={{
              background: '#0d1220',
              border: '1px solid rgba(99,102,241,0.3)',
              borderRadius: 10,
              fontSize: 12,
              color: '#f1f5f9',
            }}
            formatter={(val: any) => [`${(Number(val) * 100).toFixed(2)}%`, 'Importance']}
            labelFormatter={(f: any) => FEATURE_LABELS[String(f)] ?? String(f)}
          />
          <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
            {sorted.map((f, i) => (
              <Cell
                key={f.feature}
                fill={`hsl(${240 - i * 18}, 70%, ${65 - i * 2}%)`}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default FeatureImportanceChart;
