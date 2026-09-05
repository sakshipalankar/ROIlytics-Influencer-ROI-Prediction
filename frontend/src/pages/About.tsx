import React from 'react';
import { Info } from 'lucide-react';

const About: React.FC = () => (
  <div className="animate-fade-in">
    <div className="page-header">
      <h1 className="page-title">
        <Info size={28} />
        <span className="page-title-gradient">About ROIlytics</span>
      </h1>
      <p className="page-subtitle">Methodology, data sources, and honest limitations.</p>
    </div>

    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 900 }}>

      <div className="card">
        <div className="card-header"><span className="card-title">🎯 What ROIlytics Does</span></div>
        <div className="card-body" style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
          <p>ROIlytics predicts the <strong style={{ color: 'var(--text-primary)' }}>Return on Investment (ROI)</strong> of Instagram influencer campaigns using a trained ML model.</p>
          <p style={{ marginTop: 12 }}>It combines two data sources that would exist in a real brand/agency stack:</p>
          <ul style={{ marginTop: 8, paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 6 }}>
            <li><strong style={{ color: '#6366f1' }}>Instagram profile data</strong> — followers, engagement, posting frequency (from Instagram Business Discovery API)</li>
            <li><strong style={{ color: '#10b981' }}>Campaign economics</strong> — spend, revenue, conversions (from public Kaggle influencer marketing datasets, since platforms never expose this data)</li>
          </ul>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><span className="card-title">🔬 ML Pipeline</span></div>
        <div className="card-body">
          <table className="data-table">
            <thead><tr><th>Stage</th><th>Detail</th></tr></thead>
            <tbody>
              <tr><td>Data Collection</td><td>Instagram Business Discovery API + Kaggle datasets</td></tr>
              <tr><td>Feature Engineering</td><td>Engagement rate, log-followers, follower tier encoding, likes-to-comments ratio, category encoding</td></tr>
              <tr><td>Models Trained</td><td>Random Forest, Gradient Boosting, XGBoost, Ridge Regression, SVR</td></tr>
              <tr><td>Selection Criterion</td><td>Cross-validated R² score</td></tr>
              <tr><td>Best Model</td><td>Random Forest (typically highest CV R²)</td></tr>
              <tr><td>Target Variable</td><td>ROI = (Revenue − Spend) / Spend</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><span className="card-title">⚠️ Honest Limitations</span></div>
        <div className="card-body">
          <div className="alert alert-warn" style={{ marginBottom: 16, fontSize: 13 }}>
            The ML model is trained on simulated/publicly available data. Real-world ROI depends on brand fit, creative quality, product-market fit, and timing — factors no model can fully capture.
          </div>
          <ul style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.8, paddingLeft: 20, display: 'flex', flexDirection: 'column', gap: 6 }}>
            <li>Instagram API only accesses <strong style={{ color: 'var(--text-primary)' }}>Business or Creator accounts</strong> — personal profiles cannot be fetched</li>
            <li>Campaign spend &amp; conversion data is <strong style={{ color: 'var(--text-primary)' }}>not available</strong> from any social platform API — Kaggle data is used as a realistic proxy</li>
            <li>Predictions are estimates — use them to <em>rank and compare</em> influencer candidates, not as guaranteed returns</li>
            <li>Engagement metrics from the Kaggle dataset may not perfectly match real campaign outcomes</li>
          </ul>
        </div>
      </div>

      <div className="card">
        <div className="card-header"><span className="card-title">🛠️ Tech Stack</span></div>
        <div className="card-body">
          <div className="grid-2">
            <div>
              <div className="nav-section-label" style={{ marginBottom: 10 }}>Frontend</div>
              <ul style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 2, paddingLeft: 0, listStyle: 'none' }}>
                {['React 18 + TypeScript', 'Vite (build tool)', 'Recharts (charts)', 'Zustand (state)', 'Axios (HTTP)', 'Lucide React (icons)'].map(t => (
                  <li key={t} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-primary)', flexShrink: 0, display: 'inline-block' }} />
                    {t}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <div className="nav-section-label" style={{ marginBottom: 10 }}>Backend & ML</div>
              <ul style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 2, paddingLeft: 0, listStyle: 'none' }}>
                {['FastAPI + Uvicorn', 'Pydantic v2 (schemas)', 'scikit-learn + XGBoost', 'pandas + numpy', 'joblib (model persistence)', 'Instagram Graph API v19'].map(t => (
                  <li key={t} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-emerald)', flexShrink: 0, display: 'inline-block' }} />
                    {t}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
);

export default About;
