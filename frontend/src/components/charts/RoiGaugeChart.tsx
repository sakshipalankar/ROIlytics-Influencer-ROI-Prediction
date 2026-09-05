import React from 'react';
import {
  RadialBarChart, RadialBar, ResponsiveContainer, PolarAngleAxis
} from 'recharts';
import type { PredictResponse } from '../../types';

interface Props {
  result: PredictResponse;
}

const RoiGaugeChart: React.FC<Props> = ({ result }) => {
  // Clamp ROI to [0, 5] for display, 5 = 100%
  const clamped = Math.max(0, Math.min(result.roi, 5));
  const pct = (clamped / 5) * 100;

  const data = [{ name: 'ROI', value: pct }];

  return (
    <div style={{ textAlign: 'center', position: 'relative' }}>
      <ResponsiveContainer width="100%" height={200}>
        <RadialBarChart
          cx="50%" cy="85%"
          innerRadius="60%"
          outerRadius="100%"
          startAngle={180}
          endAngle={0}
          data={data}
          barSize={20}
        >
          <PolarAngleAxis
            type="number"
            domain={[0, 100]}
            angleAxisId={0}
            tick={false}
          />
          <RadialBar
            background={{ fill: 'rgba(255,255,255,0.04)' }}
            dataKey="value"
            cornerRadius={10}
            fill={result.tier_color}
            angleAxisId={0}
          />
        </RadialBarChart>
      </ResponsiveContainer>
      <div style={{
        position: 'absolute',
        bottom: 24,
        left: '50%',
        transform: 'translateX(-50%)',
        textAlign: 'center',
      }}>
        <div style={{
          fontSize: 36,
          fontWeight: 900,
          color: result.tier_color,
          lineHeight: 1,
          fontVariantNumeric: 'tabular-nums',
        }}>
          {result.roi.toFixed(2)}x
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
          ROI Score
        </div>
      </div>
    </div>
  );
};

export default RoiGaugeChart;
