import React from 'react';
import { useAppStore } from '../store/useAppStore';
import {
  Sparkles,
  Database,
  Cpu,
  BarChart3,
  TrendingUp,
  Calculator,
  CheckCircle2,
  ArrowRight,
  Layers,
  Search,
} from 'lucide-react';

const HowItWorks: React.FC = () => {
  const { setActivePage } = useAppStore();

  const PIPELINE_STEPS = [
    {
      step: '01',
      badge: 'Data Collection',
      title: 'Audience & Engagement Extraction',
      icon: Database,
      color: '#38bdf8',
      desc: 'Connects to Instagram Graph API (Business Discovery) to extract genuine profile attributes: follower counts, media frequency, average likes, and comments.',
      details: [
        'Calculates real engagement rate: ER = ((Likes + Comments) / Followers) × 100',
        'Profiles categorized across 10 distinct industry niches',
        'Classified into 4 industry standard tiers (Nano, Micro, Macro, Mega)',
      ],
    },
    {
      step: '02',
      badge: 'Feature Engineering',
      title: 'Bucket-Based Data Fusion',
      icon: Layers,
      color: '#a855f7',
      desc: 'Matches live creator profiles with Kaggle multi-brand campaign performance benchmarks using statistical bucket aggregation.',
      details: [
        'Overcomes missing historical ad spend via transfer-learning heuristics',
        'Derived features: Log-transformed reach, ER × Spend interaction terms',
        'Noise-augmented sampling across 628 validated campaign benchmarks',
      ],
    },
    {
      step: '03',
      badge: 'Machine Learning',
      title: 'Trained Regression Models',
      icon: Cpu,
      color: '#10b981',
      desc: 'Compares Linear Regression, Random Forest, and XGBoost regressor pipelines to predict expected revenue multipliers.',
      details: [
        'Random Forest selected as Best Model (R² = 0.578, MAE = 0.384)',
        'Pre-loaded via FastAPI lifespan for instantaneous sub-10ms predictions',
        'Output yields predicted revenue, gross profit, and multiplier tier',
      ],
    },
    {
      step: '04',
      badge: 'Campaign Optimization',
      title: 'Dynamic Fit Scoring & Budget Simulation',
      icon: Calculator,
      color: '#ffd54f',
      desc: 'Calculates a brand-specific Fit Score (0–100) and plots sensitivity curves across ad budgets from ₹5,000 to ₹5,00,000.',
      details: [
        'Fit score balances audience tier, niche synergy, and campaign objective',
        'Curves reveal sweet spots before diminishing returns reduce ROI',
        'Enables marketers to test scenarios before allocating capital',
      ],
    },
  ];

  const MODEL_METRICS = [
    { name: 'Random Forest', r2: '0.578', mae: '0.384', rmse: '0.494', status: 'Best Model (Active)', isBest: true },
    { name: 'XGBoost', r2: '0.565', mae: '0.398', rmse: '0.502', status: 'Runner-up', isBest: false },
    { name: 'Linear Regression', r2: '0.526', mae: '0.425', rmse: '0.524', status: 'Baseline', isBest: false },
  ];

  return (
    <div className="animate-fade-in how-it-works-page">
      {/* ── Hero Header ── */}
      <div className="card hiw-hero-card">
        <div className="hiw-badge">
          <Sparkles size={14} color="var(--accent-primary)" />
          <span>Under The Hood</span>
        </div>
        <h1 className="hiw-title">
          How ROIlytics Predicts <span className="page-title-gradient">Campaign ROI</span>
        </h1>
        <p className="hiw-subtitle">
          From live Instagram audience extraction to machine learning regression models and dynamic budget simulation — explore our data-driven pipeline.
        </p>

        <div className="hiw-quick-metrics">
          <div className="hiw-quick-metric">
            <span className="hiw-qm-val">10,500+</span>
            <span className="hiw-qm-lbl">Analyzed Creators</span>
          </div>
          <div className="hiw-qm-divider" />
          <div className="hiw-quick-metric">
            <span className="hiw-qm-val">R² 0.58</span>
            <span className="hiw-qm-lbl">Model Accuracy</span>
          </div>
          <div className="hiw-qm-divider" />
          <div className="hiw-quick-metric">
            <span className="hiw-qm-val">&lt; 10ms</span>
            <span className="hiw-qm-lbl">Inference Latency</span>
          </div>
          <div className="hiw-qm-divider" />
          <div className="hiw-quick-metric">
            <span className="hiw-qm-val">100%</span>
            <span className="hiw-qm-lbl">Audience Authenticity</span>
          </div>
        </div>
      </div>

      {/* ── 4-Stage Architectural Pipeline ── */}
      <div className="hiw-section-title-wrap">
        <h2 className="hiw-section-title">The 4-Stage Predictive Pipeline</h2>
        <p className="hiw-section-desc">How raw social engagement transforms into verified revenue projections</p>
      </div>

      <div className="hiw-pipeline-grid">
        {PIPELINE_STEPS.map(item => {
          const Icon = item.icon;
          return (
            <div className="card hiw-step-card" key={item.step}>
              <div className="hiw-step-top">
                <div className="hiw-step-icon" style={{ background: `${item.color}22`, color: item.color, border: `1px solid ${item.color}44` }}>
                  <Icon size={22} />
                </div>
                <div className="hiw-step-number">{item.step}</div>
              </div>

              <span className="hiw-step-badge" style={{ color: item.color }}>{item.badge}</span>
              <h3 className="hiw-step-title">{item.title}</h3>
              <p className="hiw-step-desc">{item.desc}</p>

              <div className="hiw-step-list">
                {item.details.map((detail, idx) => (
                  <div className="hiw-step-list-item" key={idx}>
                    <CheckCircle2 size={14} color="#10b981" className="hiw-check-icon" />
                    <span>{detail}</span>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Machine Learning Benchmark & Formula Section ── */}
      <div className="hiw-grid-2">
        {/* Model Benchmark Card */}
        <div className="card hiw-model-card">
          <div className="card-header" style={{ marginBottom: 16 }}>
            <div>
              <h3 className="card-title" style={{ fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                <BarChart3 size={18} color="var(--accent-primary)" />
                <span>Model Benchmark & Evaluation</span>
              </h3>
              <p className="card-subtitle">Comparing model performance across cross-validation tests</p>
            </div>
          </div>

          <table className="hiw-table">
            <thead>
              <tr>
                <th>Model Architecture</th>
                <th>R² Score</th>
                <th>MAE</th>
                <th>RMSE</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {MODEL_METRICS.map(m => (
                <tr key={m.name} className={m.isBest ? 'highlight-row' : ''}>
                  <td style={{ fontWeight: 700 }}>{m.name}</td>
                  <td style={{ fontWeight: 800, color: m.isBest ? '#10b981' : 'var(--text-primary)' }}>{m.r2}</td>
                  <td>{m.mae}</td>
                  <td>{m.rmse}</td>
                  <td>
                    <span className={`badge ${m.isBest ? 'badge-emerald' : 'badge-slate'}`}>
                      {m.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="hiw-formula-box">
            <div className="hiw-formula-title">Core Prediction Objective:</div>
            <code>ROI = Projected Revenue / Campaign Spend</code>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: '8px 0 0' }}>
              Multipliers above 2.5x represent profitable creator campaigns based on historical conversion benchmarks.
            </p>
          </div>
        </div>

        {/* Feature Importance & Drivers Card */}
        <div className="card hiw-drivers-card">
          <div className="card-header" style={{ marginBottom: 16 }}>
            <div>
              <h3 className="card-title" style={{ fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                <TrendingUp size={18} color="#38bdf8" />
                <span>Key Predictive Drivers</span>
              </h3>
              <p className="card-subtitle">Which creator attributes have the greatest impact on ROI</p>
            </div>
          </div>

          <div className="hiw-drivers-list">
            {[
              { label: 'Engagement Rate (ER)', weight: '34%', desc: 'Highest impact: Smaller creators with authentic followers yield higher conversion.' },
              { label: 'Campaign Spend Level', weight: '26%', desc: 'Ad spend relative to audience size determines marginal return rates.' },
              { label: 'Follower Tier Category', weight: '18%', desc: 'Micro creators (10K–100K) consistently deliver peak multiplier ratios.' },
              { label: 'Niche & Category Alignment', weight: '14%', desc: 'High synergy between product and creator niche boosts conversion by 40%.' },
              { label: 'Posting Frequency', weight: '8%', desc: 'Consistent posting maintains active audience interest and story views.' },
            ].map(d => (
              <div className="hiw-driver-item" key={d.label}>
                <div className="hiw-driver-top">
                  <span className="hiw-driver-name">{d.label}</span>
                  <span className="hiw-driver-weight">{d.weight}</span>
                </div>
                <div className="hiw-driver-bar-track">
                  <div className="hiw-driver-bar-fill" style={{ width: d.weight }} />
                </div>
                <div className="hiw-driver-desc">{d.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Bottom Call To Action ── */}
      <div className="card hiw-cta-card">
        <div className="hiw-cta-left">
          <h3 className="hiw-cta-title">Ready to Test Your Campaign Strategy?</h3>
          <p className="hiw-cta-desc">
            Use the discovery engine to find ranked creators tailored to your brand niche, follower tier, and budget.
          </p>
        </div>
        <div className="hiw-cta-right">
          <button
            className="btn btn-primary"
            onClick={() => setActivePage('discover')}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '12px 24px' }}
          >
            <Search size={16} />
            <span>Launch Influencer Discovery</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default HowItWorks;
