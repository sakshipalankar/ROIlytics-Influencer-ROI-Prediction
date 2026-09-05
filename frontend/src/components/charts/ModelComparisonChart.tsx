import React from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend
} from 'recharts';
import type { ModelMetric } from '../../types';

interface Props {
  models: ModelMetric[];
  bestModel: string;
}

const COLORS = ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b'];

const ModelComparisonChart: React.FC<Props> = ({ models, bestModel }) => {
  return (
    <div className="chart-container">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={models} margin={{ top: 10, right: 20, left: 0, bottom: 0 }} barGap={4}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fill: '#64748b', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[0, 1]}
            tickFormatter={v => `${(v * 100).toFixed(0)}%`}
            tick={{ fill: '#64748b', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={45}
          />
          <Tooltip
            contentStyle={{
              background: '#0d1220',
              border: '1px solid rgba(99,102,241,0.3)',
              borderRadius: 10,
              fontSize: 12,
              color: '#f1f5f9',
            }}
            formatter={(val: any, name: any) => [`${(Number(val) * 100).toFixed(1)}%`, String(name)]}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
          <Bar dataKey="r2" name="R² Score" radius={[4, 4, 0, 0]}>
            {models.map((m, i) => (
              <Cell
                key={m.name}
                fill={COLORS[i % COLORS.length]}
                opacity={m.name === bestModel ? 1 : 0.6}
              />
            ))}
          </Bar>
          <Bar dataKey="cv_r2" name="CV R²" radius={[4, 4, 0, 0]} fill="#475569" opacity={0.7} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ModelComparisonChart;
