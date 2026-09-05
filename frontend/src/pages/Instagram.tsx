import React from 'react';
import LiveApiPanel from '../components/instagram/LiveApiPanel';
import { useAppStore } from '../store/useAppStore';
import ResultKpiCards from '../components/prediction/ResultKpiCards';
import RoiGaugeChart from '../components/charts/RoiGaugeChart';
import { Smartphone } from 'lucide-react';

const InstagramPage: React.FC = () => {
  const { predictionResult } = useAppStore();
  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1 className="page-title">
          <Smartphone size={28} />
          <span className="page-title-gradient">Live Instagram</span>
        </h1>
        <p className="page-subtitle">
          Fetch real Instagram Business/Creator profiles via the Graph API and predict their ROI.
        </p>
      </div>
      <div className="grid-2" style={{ alignItems: 'start' }}>
        <div className="card">
          <div className="card-header">
            <span className="card-title">📡 Business Discovery API</span>
          </div>
          <div className="card-body">
            <LiveApiPanel />
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {predictionResult ? (
            <>
              <div className="card">
                <div className="card-header">
                  <span className="card-title">🎯 Live ROI Score</span>
                </div>
                <div className="card-body">
                  <RoiGaugeChart result={predictionResult} />
                </div>
              </div>
              <div className="card">
                <div className="card-header">
                  <span className="card-title">📈 Predicted Metrics</span>
                </div>
                <div className="card-body">
                  <ResultKpiCards result={predictionResult} />
                </div>
              </div>
            </>
          ) : (
            <div className="card">
              <div className="card-body" style={{ textAlign: 'center', padding: '60px 24px' }}>
                <div style={{ fontSize: 56, marginBottom: 16 }}>📱</div>
                <div style={{ fontWeight: 700, fontSize: 18, marginBottom: 8 }}>Live Prediction</div>
                <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
                  Fetch an Instagram profile on the left, set your campaign budget, and click Predict to see live ROI estimates.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default InstagramPage;
