import React, { useEffect, useState } from 'react';
import PredictionForm from '../components/prediction/PredictionForm';
import ResultKpiCards from '../components/prediction/ResultKpiCards';
import RoiGaugeChart from '../components/charts/RoiGaugeChart';
import BudgetSimChart from '../components/charts/BudgetSimChart';
import BatchUpload from '../components/prediction/BatchUpload';
import { useAppStore } from '../store/useAppStore';
import { getAnalyticsOverview } from '../api/client';
import { simulateBudget } from '../api/client';
import type { SimulatePoint } from '../types';
import { LayoutDashboard, Upload } from 'lucide-react';

const Dashboard: React.FC = () => {
  const { predictionResult, overview, setOverview } = useAppStore();
  const [simPoints, setSimPoints] = useState<SimulatePoint[]>([]);
  const [activeTab, setActiveTab] = useState<'manual' | 'batch'>('manual');

  useEffect(() => {
    if (!overview) {
      getAnalyticsOverview()
        .then(setOverview)
        .catch(console.error);
    }
  }, []);

  useEffect(() => {
    if (!predictionResult) return;
    const { engagement_rate, follower_tier } = predictionResult;
    // Rough followers estimate from tier
    const followerMap: Record<string, number> = {
      Nano: 5000, Micro: 50000, Macro: 400000, Mega: 2000000
    };
    const followers = followerMap[follower_tier] ?? 50000;
    const avg_likes = Math.round(followers * engagement_rate * 0.9);
    const avg_comments = Math.round(followers * engagement_rate * 0.1);

    simulateBudget({
      followers_count: followers,
      media_count: 300,
      avg_likes,
      avg_comments,
      category: 'Lifestyle',
      posting_frequency: 3.5,
      spend: 0, // unused in simulate
      spend_min: 500,
      spend_max: 50000,
      steps: 25,
    }).then(r => setSimPoints(r.points)).catch(console.error);
  }, [predictionResult]);

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1 className="page-title">
          <LayoutDashboard size={28} />
          <span className="page-title-gradient">ROI Predictor</span>
        </h1>
        <p className="page-subtitle">
          Predict the return on investment for any Instagram influencer campaign using our trained ML model.
        </p>
      </div>

      {/* Mode Tabs */}
      <div className="tabs">
        <button
          id="tab-manual"
          className={`tab${activeTab === 'manual' ? ' active' : ''}`}
          onClick={() => setActiveTab('manual')}
        >
          Manual Predict
        </button>
        <button
          id="tab-batch"
          className={`tab${activeTab === 'batch' ? ' active' : ''}`}
          onClick={() => setActiveTab('batch')}
        >
          <Upload size={14} style={{ display: 'inline', marginRight: 4 }} />
          Batch Upload
        </button>
      </div>

      {activeTab === 'manual' ? (
        <div className="grid-2" style={{ alignItems: 'start' }}>
          {/* Left: Form */}
          <div>
            <PredictionForm overview={overview} />
          </div>

          {/* Right: Results */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {predictionResult ? (
              <>
                {/* Gauge */}
                <div className="card">
                  <div className="card-header">
                    <span className="card-title">🎯 ROI Score</span>
                    <span
                      className="tier-pill"
                      style={{
                        color: predictionResult.tier_color,
                        borderColor: predictionResult.tier_color + '55',
                        background: predictionResult.tier_color + '18',
                      }}
                    >
                      {predictionResult.tier}
                    </span>
                  </div>
                  <div className="card-body">
                    <RoiGaugeChart result={predictionResult} />
                  </div>
                </div>

                {/* KPI Cards */}
                <div className="card">
                  <div className="card-header">
                    <span className="card-title">📈 Campaign Metrics</span>
                  </div>
                  <div className="card-body">
                    <ResultKpiCards result={predictionResult} />
                  </div>
                </div>

                {/* Budget Simulator */}
                {simPoints.length > 0 && (
                  <div className="card">
                    <div className="card-header">
                      <span className="card-title">💰 Budget Simulation</span>
                    </div>
                    <div className="card-body">
                      <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>
                        How revenue & profit scale with spend for this influencer profile.
                      </p>
                      <BudgetSimChart points={simPoints} />
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="card" style={{ textAlign: 'center' }}>
                <div className="card-body" style={{ padding: '60px 24px' }}>
                  <div style={{ fontSize: 56, marginBottom: 16 }}>🎯</div>
                  <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>
                    Ready to Predict
                  </div>
                  <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
                    Fill in the influencer metrics on the left and click <strong>Predict ROI</strong>.
                    Results will appear here with a visual gauge, KPI cards, and budget simulation.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="card-header">
            <span className="card-title">📁 Batch CSV Predictions</span>
          </div>
          <div className="card-body">
            <BatchUpload />
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
