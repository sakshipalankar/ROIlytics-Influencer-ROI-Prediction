import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import type { SimulatePoint } from '../../types';

interface Props {
  points: SimulatePoint[];
}

const fmtINR = (v: number) => `Rs. ${Math.round(v).toLocaleString('en-IN')}`;

const BudgetSimChart: React.FC<Props> = ({ points }) => {
  return (
    <div className="chart-container">
      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={points} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
          <defs>
            <linearGradient id="grad-revenue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="grad-profit" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="grad-spend" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="spend"
            tickFormatter={v => `Rs. ${(v / 1000).toFixed(0)}K`}
            tick={{ fill: '#64748b', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tickFormatter={v => `Rs. ${(v / 1000).toFixed(0)}K`}
            tick={{ fill: '#64748b', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={65}
          />
          <Tooltip
            contentStyle={{
              background: '#0d1220',
              border: '1px solid rgba(99,102,241,0.3)',
              borderRadius: 10,
              fontSize: 12,
              color: '#f1f5f9',
            }}
            formatter={(val: any, name: any) => [fmtINR(Number(val)), String(name).charAt(0).toUpperCase() + String(name).slice(1)]}
            labelFormatter={(label: any) => `Spend: ${fmtINR(Number(label))}`}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
          <Area type="monotone" dataKey="revenue" stroke="#6366f1" strokeWidth={2} fill="url(#grad-revenue)" name="Revenue" />
          <Area type="monotone" dataKey="profit"  stroke="#10b981" strokeWidth={2} fill="url(#grad-profit)"  name="Profit"  />
          <Area type="monotone" dataKey="spend"   stroke="#f59e0b" strokeWidth={2} fill="url(#grad-spend)"   name="Spend"   strokeDasharray="4 4" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default BudgetSimChart;
