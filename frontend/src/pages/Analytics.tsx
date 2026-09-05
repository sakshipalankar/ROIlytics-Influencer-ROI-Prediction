import React, { useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { getModelResults, getAnalyticsOverview } from '../api/client';
import ModelComparisonChart from '../components/charts/ModelComparisonChart';
import FeatureImportanceChart from '../components/charts/FeatureImportanceChart';
import { BarChart3 } from 'lucide-react';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid
} from 'recharts';

const CATEGORY_COLORS = ['#6366f1', '#8b5cf6', '#10b981', '#f59e0b', '#f43f5e', '#38bdf8'];

const Analytics: React.FC = () => {
  const { modelResults, setModelResults, overview, setOverview } = useAppStore();

  useEffect(() => {
    if (!modelResults) getModelResults().then(setModelResults).catch(console.error);
    if (!overview) getAnalyticsOverview().then(setOverview).catch(console.error);
  }, []);

  const catData = overview
    ? Object.entries(overview.category_distribution).map(([k, v]) => ({ name: k, value: v }))
    : [];

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1 className="page-title">
          <BarChart3 size={28} />
          <span className="page-title-gradient">Analytics</span>
        </h1>
        <p className="page-subtitle">
          Model performance benchmarks, feature importance, and dataset insights.
        </p>
      </div>

      {/* Dataset Overview KPIs */}
      {overview && (
        <div className="kpi-grid" style={{ marginBottom: 24 }}>
          <div className="kpi-card" style={{ '--kpi-accent': '#6366f1' } as React.CSSProperties}>
            <div className="kpi-label">Total Profiles</div>
            <div className="kpi-value">{overview.total_profiles}</div>
            <div className="kpi-sub">Training dataset</div>
          </div>
          <div className="kpi-card" style={{ '--kpi-accent': '#10b981' } as React.CSSProperties}>
            <div className="kpi-label">Avg ROI</div>
            <div className="kpi-value">{overview.avg_roi.toFixed(2)}x</div>
            <div className="kpi-sub">Across all profiles</div>
          </div>
          <div className="kpi-card" style={{ '--kpi-accent': '#38bdf8' } as React.CSSProperties}>
            <div className="kpi-label">Avg Engagement</div>
            <div className="kpi-value">{(overview.avg_engagement_rate * 100).toFixed(2)}%</div>
            <div className="kpi-sub">Mean engagement rate</div>
          </div>
          <div className="kpi-card" style={{ '--kpi-accent': '#f59e0b' } as React.CSSProperties}>
            <div className="kpi-label">Top Category</div>
            <div className="kpi-value" style={{ fontSize: 18 }}>{overview.top_category}</div>
            <div className="kpi-sub">Most common niche</div>
          </div>
          {modelResults && (
            <div className="kpi-card" style={{ '--kpi-accent': '#8b5cf6' } as React.CSSProperties}>
              <div className="kpi-label">Best Model</div>
              <div className="kpi-value" style={{ fontSize: 16 }}>{modelResults.best_model}</div>
              <div className="kpi-sub">{modelResults.training_samples} training samples</div>
            </div>
          )}
        </div>
      )}

      <div className="grid-2" style={{ marginBottom: 24 }}>
        {/* Model Comparison */}
        {modelResults && modelResults.models.length > 0 ? (
          <div className="card">
            <div className="card-header">
              <span className="card-title">🏆 Model Benchmark</span>
              <span className="badge badge-indigo">{modelResults.best_model}</span>
            </div>
            <div className="card-body">
              <ModelComparisonChart models={modelResults.models} bestModel={modelResults.best_model} />
              {/* MAE / RMSE table */}
              <table className="data-table" style={{ marginTop: 16 }}>
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>R²</th>
                    <th>MAE</th>
                    <th>RMSE</th>
                    <th>CV R²</th>
                  </tr>
                </thead>
                <tbody>
                  {modelResults.models.map(m => (
                    <tr key={m.name}>
                      <td style={{ fontWeight: m.name === modelResults.best_model ? 700 : 400, color: m.name === modelResults.best_model ? 'var(--accent-primary)' : undefined }}>
                        {m.name} {m.name === modelResults.best_model && '⭐'}
                      </td>
                      <td className="font-mono">{(m.r2 * 100).toFixed(1)}%</td>
                      <td className="font-mono">{m.mae.toFixed(3)}</td>
                      <td className="font-mono">{m.rmse.toFixed(3)}</td>
                      <td className="font-mono">{(m.cv_r2 * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="card">
            <div className="card-body loader-overlay">
              <div className="spinner" /> Loading model results…
            </div>
          </div>
        )}

        {/* Category Distribution */}
        {catData.length > 0 && (
          <div className="card">
            <div className="card-header">
              <span className="card-title">📊 Category Distribution</span>
            </div>
            <div className="card-body">
              <div className="chart-container">
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie
                      data={catData}
                      cx="50%" cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {catData.map((_, i) => (
                        <Cell key={i} fill={CATEGORY_COLORS[i % CATEGORY_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: '#0d1220',
                        border: '1px solid rgba(99,102,241,0.3)',
                        borderRadius: 10,
                        fontSize: 12,
                        color: '#f1f5f9',
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Feature Importance */}
      {modelResults && modelResults.feature_importance.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header">
            <span className="card-title">🔍 Feature Importance</span>
          </div>
          <div className="card-body">
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
              Which influencer attributes most strongly predict ROI?
            </p>
            <FeatureImportanceChart features={modelResults.feature_importance} />
          </div>
        </div>
      )}

      {/* ROI Distribution */}
      {overview && overview.roi_distribution.length > 0 && (
        <div className="card">
          <div className="card-header">
            <span className="card-title">📈 ROI Distribution</span>
          </div>
          <div className="card-body">
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={overview.roi_distribution} margin={{ top: 0, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis dataKey="label" tick={{ fill: '#64748b', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} width={30} />
                  <Tooltip
                    contentStyle={{ background: '#0d1220', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 10, fontSize: 12, color: '#f1f5f9' }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]} fill="#6366f1" name="Profiles" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Analytics;
