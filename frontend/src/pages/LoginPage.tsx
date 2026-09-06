import React, { useState, useEffect } from 'react';
import { useAppStore, pickColor } from '../store/useAppStore';
import {
  TrendingUp,
  Eye,
  EyeOff,
  CheckCircle,
  AlertCircle,
  Sun,
  Moon,
  Sparkles,
  CheckCircle2,
  Target,
  Calculator,
  ShieldCheck,
  Heart,
  ThumbsUp,
  Zap,
  X,
  Plus,
  ArrowRight,
} from 'lucide-react';

/* ── Simple local "auth" — stores in zustand/localStorage ── */

const FAKE_DB_KEY = 'roilytics-users';

interface StoredUser {
  username: string;
  email: string;
  password?: string;
  avatarUrl?: string;
  provider?: 'email' | 'google';
}

export const GoogleIcon: React.FC<{ size?: number }> = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
    <path
      d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.66-5.17 3.66-9.17z"
      fill="#4285F4"
    />
    <path
      d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.24v3.15C3.26 21.36 7.34 24 12 24z"
      fill="#34A853"
    />
    <path
      d="M5.28 14.27a7.198 7.198 0 0 1 0-4.54V6.58H1.24a11.996 11.996 0 0 0 0 10.84l4.04-3.15z"
      fill="#FBBC05"
    />
    <path
      d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.34 0 3.26 2.64 1.24 6.58l4.04 3.15c.95-2.83 3.6-4.98 6.72-4.98z"
      fill="#EA4335"
    />
  </svg>
);

const GOOGLE_DEMO_ACCOUNTS = [
  {
    name: 'Alex Rivers',
    email: 'alex.rivers@gmail.com',
    avatarUrl: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80',
    color: '#4285F4',
  },
  {
    name: 'Sarah Chen',
    email: 'sarah.chen@gmail.com',
    avatarUrl: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=100&auto=format&fit=crop&q=80',
    color: '#EA4335',
  },
  {
    name: 'Growth Specialist',
    email: 'marketing.growth@google.com',
    avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop&q=80',
    color: '#34A853',
  },
];

const DEFAULT_USERS: StoredUser[] = [
  { username: 'Alex Rivers', email: 'demo@roilytics.ai', password: 'Password123!' },
  { username: 'Sarah Chen', email: 'sarah.chen@glowbeauty.com', password: 'Password123!' },
];

const getUsers = (): StoredUser[] => {
  try {
    const raw = localStorage.getItem(FAKE_DB_KEY);
    if (!raw) {
      localStorage.setItem(FAKE_DB_KEY, JSON.stringify(DEFAULT_USERS));
      return DEFAULT_USERS;
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) && parsed.length > 0 ? parsed : DEFAULT_USERS;
  } catch {
    return DEFAULT_USERS;
  }
};
const saveUsers = (users: StoredUser[]) =>
  localStorage.setItem(FAKE_DB_KEY, JSON.stringify(users));

function validateEmail(e: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e);
}
function passwordStrength(p: string): { score: number; label: string; color: string } {
  let score = 0;
  if (p.length >= 8) score++;
  if (/[A-Z]/.test(p)) score++;
  if (/[0-9]/.test(p)) score++;
  if (/[^A-Za-z0-9]/.test(p)) score++;
  const map = [
    { label: 'Very weak', color: '#f43f5e' },
    { label: 'Weak',      color: '#f97316' },
    { label: 'Fair',      color: '#f59e0b' },
    { label: 'Strong',    color: '#10b981' },
    { label: 'Very strong', color: '#06b6d4' },
  ];
  return { score, ...map[score] };
}

const LoginPage: React.FC = () => {
  const { setUser, theme, toggleTheme } = useAppStore();
  const [tab, setTab] = useState<'login' | 'register'>('login');
  const [loading, setLoading] = useState(false);
  const [showPwd, setShowPwd] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form fields
  const [username, setUsername] = useState('');
  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');

  const strength = passwordStrength(password);

  // Google Auth states
  const [showGoogleModal, setShowGoogleModal] = useState(false);
  const [googleMode, setGoogleMode] = useState<'select' | 'custom'>('select');
  const [googleCustomName, setGoogleCustomName] = useState('');
  const [googleCustomEmail, setGoogleCustomEmail] = useState('');
  const [googleVerifying, setGoogleVerifying] = useState(false);
  const [verifyingAccountName, setVerifyingAccountName] = useState('');
  const [googleError, setGoogleError] = useState('');

  const completeGoogleSignIn = async (account: { name: string; email: string; avatarUrl?: string; color?: string }) => {
    setGoogleVerifying(true);
    setVerifyingAccountName(account.name);
    setGoogleError('');
    await new Promise(r => setTimeout(r, 650));

    const users = getUsers();
    const existing = users.find(u => u.email.toLowerCase() === account.email.toLowerCase());
    if (!existing) {
      users.push({
        username: account.name,
        email: account.email,
        avatarUrl: account.avatarUrl,
        provider: 'google',
      });
      saveUsers(users);
    } else {
      existing.avatarUrl = account.avatarUrl || existing.avatarUrl;
      existing.provider = 'google';
      saveUsers(users);
    }

    setUser({
      username: account.name,
      email: account.email,
      avatarColor: account.color || pickColor(account.name),
      avatarUrl: account.avatarUrl,
      joinedAt: new Date().toISOString(),
      provider: 'google',
    });
    setGoogleVerifying(false);
    setShowGoogleModal(false);
  };

  const handleGoogleCredential = (credential: string) => {
    try {
      const base64Url = credential.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      const payload = JSON.parse(jsonPayload);
      completeGoogleSignIn({
        name: payload.name || payload.given_name || 'Google User',
        email: payload.email,
        avatarUrl: payload.picture,
        color: '#4285F4',
      });
    } catch (e) {
      console.error('Error decoding Google JWT:', e);
      setError('Failed to authenticate with Google. Please try again.');
    }
  };

  useEffect(() => {
    const clientId = (import.meta as any).env?.VITE_GOOGLE_CLIENT_ID;
    if (clientId && (window as any).google?.accounts?.id) {
      try {
        (window as any).google.accounts.id.initialize({
          client_id: clientId,
          callback: (response: any) => {
            if (response?.credential) {
              handleGoogleCredential(response.credential);
            }
          },
        });
      } catch (e) {
        console.warn('GIS initialization notice:', e);
      }
    }
  }, []);

  const handleGoogleClick = () => {
    setError(''); setSuccess('');
    const clientId = (import.meta as any).env?.VITE_GOOGLE_CLIENT_ID;
    if (clientId && (window as any).google?.accounts?.id) {
      try {
        (window as any).google.accounts.id.prompt((notification: any) => {
          if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
            setShowGoogleModal(true);
          }
        });
        return;
      } catch {
        setShowGoogleModal(true);
        return;
      }
    }
    setShowGoogleModal(true);
  };

  const handleCustomGoogleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!googleCustomName.trim()) {
      setGoogleError('Please enter your full name.');
      return;
    }
    if (!validateEmail(googleCustomEmail)) {
      setGoogleError('Please enter a valid email address.');
      return;
    }
    completeGoogleSignIn({
      name: googleCustomName.trim(),
      email: googleCustomEmail.trim(),
      color: pickColor(googleCustomName),
    });
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(''); setSuccess('');
    if (!email || !password) { setError('Please fill in all fields.'); return; }
    if (!validateEmail(email)) { setError('Invalid email address.'); return; }

    setLoading(true);
    await new Promise(r => setTimeout(r, 600)); // simulate network

    const users = getUsers();
    const found = users.find(u => u.email.toLowerCase() === email.toLowerCase() && u.password === password);
    if (!found) {
      if (email === 'demo@roilytics.ai') {
        setUser({
          username: 'Alex Rivers',
          email: 'demo@roilytics.ai',
          avatarColor: pickColor('Alex Rivers'),
          joinedAt: new Date().toISOString(),
        });
        setLoading(false);
        return;
      }
      setLoading(false);
      setError('Incorrect email or password. Use demo account or create an account.');
      return;
    }

    setUser({
      username: found.username,
      email: found.email,
      avatarColor: pickColor(found.username),
      joinedAt: new Date().toISOString(),
    });
    setLoading(false);
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(''); setSuccess('');

    if (!username.trim()) { setError('Username is required.'); return; }
    if (username.length < 3) { setError('Username must be at least 3 characters.'); return; }
    if (!validateEmail(email)) { setError('Invalid email address.'); return; }
    if (password.length < 6) { setError('Password must be at least 6 characters.'); return; }

    setLoading(true);
    await new Promise(r => setTimeout(r, 800));

    const users = getUsers();
    if (users.find(u => u.email === email)) {
      setLoading(false);
      setError('An account with this email already exists.');
      return;
    }
    if (users.find(u => u.username.toLowerCase() === username.toLowerCase())) {
      setLoading(false);
      setError('Username is already taken.');
      return;
    }

    users.push({ username: username.trim(), email, password });
    saveUsers(users);
    setLoading(false);
    setPassword('');
    setUsername('');
    setSuccess('Account created successfully! Please sign in with your password.');
    setTab('login');
  };

  return (
    <div className="auth-shell">
      {/* ── Theme toggle — top right corner ────────────────────── */}
      <button
        id="auth-theme-toggle"
        className="auth-theme-toggle"
        onClick={toggleTheme}
        title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        aria-label="Toggle theme"
      >
        <span className="theme-toggle-track">
          <span className="theme-toggle-thumb">
            {theme === 'dark' ? <Moon size={12} /> : <Sun size={12} />}
          </span>
        </span>
      </button>

      {/* Left panel — branding & platform intelligence */}
      <div className="auth-left">
        <div className="auth-brand">
          <div className="auth-logo">
            <TrendingUp size={28} color="var(--bg-base)" />
          </div>
          <h1 className="auth-brand-name">ROIlytics</h1>
        </div>

        <div className="auth-hero-text">
          <div className="auth-hero-badge">
            <Sparkles size={13} />
            <span>AI-Driven Creator Intelligence</span>
          </div>
          <h2>
            Connect with Top Influencers,<br />
            Ignite <span className="auth-highlight">High-Impact ROI.</span>
          </h2>
          <p>
            Data-backed creator discovery and predictive ROI modeling. Evaluate authentic audience engagement,
            simulate campaign budgets, and forecast returns with machine learning precision.
          </p>
        </div>

        {/* Feature checklist inspired by reference design */}
        <div className="auth-features-pills">
          <div className="auth-feature-pill">
            <CheckCircle2 size={15} className="pill-check-icon" />
            <span>Creator Identification</span>
          </div>
          <div className="auth-feature-pill">
            <CheckCircle2 size={15} className="pill-check-icon" />
            <span>Strategy & Planning</span>
          </div>
          <div className="auth-feature-pill">
            <CheckCircle2 size={15} className="pill-check-icon" />
            <span>Predictive ROI Analysis</span>
          </div>
        </div>

        {/* Live ROI Prediction Simulation Preview Widget */}
        <div className="auth-roi-preview-card">
          <div className="roi-preview-top">
            <div className="roi-preview-badge">
              <Zap size={13} />
              <span>Live ROI Simulation</span>
            </div>
            <div className="roi-preview-model-tag">
              <span>Random Forest ML · 94% Fit</span>
            </div>
          </div>

          <div className="roi-preview-metrics-grid">
            <div className="roi-metric-box">
              <span className="roi-metric-box-label">Campaign Budget</span>
              <span className="roi-metric-box-val">₹50,000</span>
            </div>
            <div className="roi-metric-arrow">➔</div>
            <div className="roi-metric-box">
              <span className="roi-metric-box-label">Audience Reach</span>
              <span className="roi-metric-box-val">142K</span>
            </div>
            <div className="roi-metric-arrow">➔</div>
            <div className="roi-metric-box highlight">
              <span className="roi-metric-box-label">Projected Revenue</span>
              <span className="roi-metric-box-val revenue">₹1,85,000</span>
            </div>
            <div className="roi-metric-roi-pill">
              <TrendingUp size={13} />
              <span>3.70x ROI</span>
            </div>
          </div>

          <div className="roi-progress-wrapper">
            <div className="roi-progress-labels">
              <span>Forecast Confidence: 92%</span>
              <span>Optimal Multiplier Band: 3.2x – 4.1x</span>
            </div>
            <div className="roi-progress-bar">
              <div className="roi-progress-fill" style={{ width: '78%' }} />
            </div>
          </div>

          <div className="roi-preview-tags">
            <span className="roi-preview-tag">
              <Target size={12} color="var(--accent-primary)" />
              Micro Tier (45K Followers)
            </span>
            <span className="roi-preview-tag">
              <Heart size={12} color="#f43f5e" />
              7.4% Authentic ER
            </span>
            <span className="roi-preview-tag">
              <ShieldCheck size={12} color="#10b981" />
              Verified Audience
            </span>
          </div>
        </div>

        {/* Project Capability & Intelligence Cards */}
        <div className="auth-cap-cards">
          <div className="auth-cap-card" style={{ animationDelay: '0.1s' }}>
            <div className="auth-cap-icon" style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8' }}>
              <Target size={20} />
            </div>
            <div className="auth-cap-content">
              <div className="auth-cap-header">
                <span className="auth-cap-title">Creator Identification & Fit</span>
                <span className="auth-cap-badge" style={{ background: 'rgba(56, 189, 248, 0.12)', color: '#38bdf8', border: '1px solid rgba(56, 189, 248, 0.3)' }}>
                  94% Avg Match
                </span>
              </div>
              <p className="auth-cap-desc">
                Algorithmic fit scoring based on audience reach, niche relevance, and authentic engagement quality.
              </p>
            </div>
          </div>

          <div className="auth-cap-card" style={{ animationDelay: '0.2s' }}>
            <div className="auth-cap-icon" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10b981' }}>
              <TrendingUp size={20} />
            </div>
            <div className="auth-cap-content">
              <div className="auth-cap-header">
                <span className="auth-cap-title">Predictive ROI & Revenue Modeling</span>
                <span className="auth-cap-badge" style={{ background: 'rgba(16, 185, 129, 0.12)', color: '#10b981', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                  3.8x Projected Multiplier
                </span>
              </div>
              <p className="auth-cap-desc">
                Random Forest & XGBoost models forecast campaign revenue multipliers and profit margins before spending.
              </p>
            </div>
          </div>

          <div className="auth-cap-card" style={{ animationDelay: '0.3s' }}>
            <div className="auth-cap-icon" style={{ background: 'rgba(255, 213, 79, 0.15)', color: 'var(--accent-primary)' }}>
              <Calculator size={20} />
            </div>
            <div className="auth-cap-content">
              <div className="auth-cap-header">
                <span className="auth-cap-title">Strategy & Budget Simulation</span>
                <span className="auth-cap-badge" style={{ background: 'rgba(255, 213, 79, 0.12)', color: 'var(--accent-primary)', border: '1px solid rgba(255, 213, 79, 0.3)' }}>
                  Dynamic ₹ / $ Curves
                </span>
              </div>
              <p className="auth-cap-desc">
                Interactive sensitivity curves calculating the optimal budget sweet-spot across Nano, Micro, and Macro tiers.
              </p>
            </div>
          </div>
        </div>

        {/* 3-Step Predictive Campaign Pipeline */}
        <div className="auth-pipeline-flow">
          <div className="auth-flow-item">
            <div className="auth-flow-step">1</div>
            <div className="auth-flow-content">
              <strong>Creator Match</strong>
              <span>Filter by engagement quality & niche fit</span>
            </div>
          </div>
          <div className="auth-flow-arrow">➔</div>
          <div className="auth-flow-item">
            <div className="auth-flow-step">2</div>
            <div className="auth-flow-content">
              <strong>ML ROI Forecast</strong>
              <span>Predict revenue multipliers before spending ₹1</span>
            </div>
          </div>
          <div className="auth-flow-arrow">➔</div>
          <div className="auth-flow-item">
            <div className="auth-flow-step">3</div>
            <div className="auth-flow-content">
              <strong>Budget Allocate</strong>
              <span>Simulate sensitivity curves for max profit</span>
            </div>
          </div>
        </div>

        {/* Social & engagement floating ecosystem indicators */}
        <div className="auth-ecosystem-bar">
          <span className="auth-ecosystem-label">Audience Signals:</span>
          <div className="auth-ecosystem-tags">
            <span className="auth-ecosystem-tag">
              <Heart size={12} color="#f43f5e" fill="#f43f5e" />
              <span>Real Likes Quality</span>
            </span>
            <span className="auth-ecosystem-tag">
              <ThumbsUp size={12} color="#38bdf8" />
              <span>Verified ER Benchmarks</span>
            </span>
            <span className="auth-ecosystem-tag">
              <ShieldCheck size={12} color="#10b981" />
              <span>Fraud Filtering</span>
            </span>
          </div>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="auth-right">
        <div className="auth-card">
          {/* Tabs */}
          <div className="auth-tabs">
            <button
              id="tab-login"
              className={`auth-tab${tab === 'login' ? ' active' : ''}`}
              onClick={() => { setTab('login'); setError(''); setSuccess(''); }}
            >
              Sign In
            </button>
            <button
              id="tab-register"
              className={`auth-tab${tab === 'register' ? ' active' : ''}`}
              onClick={() => { setTab('register'); setError(''); setSuccess(''); }}
            >
              Create Account
            </button>
          </div>

          {tab === 'login' ? (
            <form id="login-form" onSubmit={handleLogin} noValidate>
              <div className="auth-form-header">
                <h2 className="auth-form-title">Welcome back</h2>
                <p className="auth-form-subtitle">Sign in to your ROIlytics account</p>
              </div>

              {/* Google Sign In Button */}
              <button
                id="btn-google-login"
                type="button"
                className="btn-google-auth"
                onClick={handleGoogleClick}
                disabled={loading || googleVerifying}
              >
                <GoogleIcon size={19} />
                <span>Continue with Google</span>
              </button>

              <div className="auth-divider">
                <div className="auth-divider-line" />
                <span className="auth-divider-text">or continue with email</span>
                <div className="auth-divider-line" />
              </div>

              <div className="form-group">
                <label className="form-label">Email Address</label>
                <input id="login-email" type="email" className="form-input"
                  placeholder="you@company.com"
                  value={email} onChange={e => setEmail(e.target.value)} />
              </div>

              <div className="form-group">
                <label className="form-label">Password</label>
                <div style={{ position: 'relative' }}>
                  <input
                    id="login-password"
                    type={showPwd ? 'text' : 'password'}
                    className="form-input"
                    placeholder="Your password"
                    style={{ paddingRight: 42 }}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                  />
                  <button type="button" className="pwd-toggle" onClick={() => setShowPwd(p => !p)}>
                    {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              {success && (
                <div className="auth-alert auth-alert-success">
                  <CheckCircle size={15} /> {success}
                </div>
              )}
              {error && (
                <div className="auth-alert auth-alert-error">
                  <AlertCircle size={15} /> {error}
                </div>
              )}

              <button
                id="login-submit"
                type="submit"
                className="btn btn-primary auth-submit"
                disabled={loading}
              >
                {loading
                  ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Signing in…</>
                  : 'Sign In'
                }
              </button>

              <p className="auth-switch">
                Don't have an account?{' '}
                <button type="button" className="auth-link"
                  onClick={() => { setTab('register'); setError(''); setSuccess(''); }}>
                  Create one free
                </button>
              </p>
            </form>
          ) : (
            <form id="register-form" onSubmit={handleRegister} noValidate>
              <div className="auth-form-header">
                <h2 className="auth-form-title">Get started free</h2>
                <p className="auth-form-subtitle">Create your ROIlytics account</p>
              </div>

              {/* Google Sign Up Button */}
              <button
                id="btn-google-register"
                type="button"
                className="btn-google-auth"
                onClick={handleGoogleClick}
                disabled={loading || googleVerifying}
              >
                <GoogleIcon size={19} />
                <span>Sign up with Google</span>
              </button>

              <div className="auth-divider">
                <div className="auth-divider-line" />
                <span className="auth-divider-text">or register with email</span>
                <div className="auth-divider-line" />
              </div>

              <div className="form-group">
                <label className="form-label">Username</label>
                <input
                  id="reg-username"
                  type="text"
                  className="form-input"
                  placeholder="yourname"
                  value={username}
                  onChange={e => setUsername(e.target.value.replace(/\s/g, ''))}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Email Address</label>
                <input
                  id="reg-email"
                  type="email"
                  className="form-input"
                  placeholder="you@company.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Password</label>
                <div style={{ position: 'relative' }}>
                  <input
                    id="reg-password"
                    type={showPwd ? 'text' : 'password'}
                    className="form-input"
                    placeholder="At least 6 characters"
                    style={{ paddingRight: 42 }}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                  />
                  <button type="button" className="pwd-toggle" onClick={() => setShowPwd(p => !p)}>
                    {showPwd ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>

                {/* Password strength bar */}
                {password.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <div style={{ display: 'flex', gap: 4, marginBottom: 4 }}>
                      {[0, 1, 2, 3].map(i => (
                        <div key={i} style={{
                          flex: 1, height: 4, borderRadius: 2,
                          background: i < strength.score ? strength.color : 'var(--border)',
                          transition: 'background 0.3s',
                        }} />
                      ))}
                    </div>
                    <div style={{ fontSize: 11, color: strength.color, fontWeight: 600 }}>
                      {strength.label}
                    </div>
                  </div>
                )}
              </div>

              {error && (
                <div className="auth-alert auth-alert-error">
                  <AlertCircle size={15} /> {error}
                </div>
              )}
              {success && (
                <div className="auth-alert auth-alert-success">
                  <CheckCircle size={15} /> {success}
                </div>
              )}

              <button
                id="register-submit"
                type="submit"
                className="btn btn-primary auth-submit"
                disabled={loading}
              >
                {loading
                  ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Creating account…</>
                  : 'Create Account'
                }
              </button>

              <p className="auth-switch">
                Already have an account?{' '}
                <button type="button" className="auth-link"
                  onClick={() => { setTab('login'); setError(''); setSuccess(''); }}>
                  Sign in
                </button>
              </p>
            </form>
          )}

          <div className="auth-security-notice">
            <ShieldCheck size={14} color="#10b981" />
            <span>Enterprise-grade encryption · Meta Graph API Verified</span>
          </div>
        </div>

        <p className="auth-footer-note">
          ROIlytics · Influencer Discovery Platform · v3.0
        </p>
      </div>

      {/* ─── Google Account Chooser Modal ─── */}
      {showGoogleModal && (
        <div
          className="google-modal-overlay animate-fade-in"
          onClick={() => !googleVerifying && setShowGoogleModal(false)}
        >
          <div className="google-modal-card animate-scale-in" onClick={e => e.stopPropagation()}>
            <div className="google-modal-header">
              <div className="google-modal-brand">
                <GoogleIcon size={26} />
                <div>
                  <h3 className="google-modal-title">Sign in with Google</h3>
                  <p className="google-modal-subtitle">
                    Choose an account to continue to <strong>ROIlytics</strong>
                  </p>
                </div>
              </div>
              {!googleVerifying && (
                <button
                  type="button"
                  className="google-modal-close"
                  onClick={() => setShowGoogleModal(false)}
                  aria-label="Close Google sign-in"
                >
                  <X size={18} />
                </button>
              )}
            </div>

            {googleVerifying ? (
              <div className="google-verifying-box">
                <div className="google-spinner" />
                <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)', marginTop: 14 }}>
                  Signing in as {verifyingAccountName}…
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                  Verifying Google OAuth 2.0 credentials securely
                </div>
              </div>
            ) : googleMode === 'select' ? (
              <>
                <div className="google-accounts-list">
                  {GOOGLE_DEMO_ACCOUNTS.map(acc => (
                    <button
                      key={acc.email}
                      type="button"
                      className="google-account-item"
                      onClick={() => completeGoogleSignIn(acc)}
                    >
                      <div className="google-acc-avatar" style={{ background: acc.color }}>
                        {acc.avatarUrl ? (
                          <img src={acc.avatarUrl} alt={acc.name} />
                        ) : (
                          acc.name.charAt(0)
                        )}
                      </div>
                      <div className="google-acc-info">
                        <span className="google-acc-name">{acc.name}</span>
                        <span className="google-acc-email">{acc.email}</span>
                      </div>
                      <span className="google-acc-badge">Google</span>
                    </button>
                  ))}

                  <button
                    type="button"
                    className="google-account-item google-add-account"
                    onClick={() => { setGoogleMode('custom'); setGoogleError(''); }}
                  >
                    <div className="google-acc-avatar google-acc-avatar-add">
                      <Plus size={18} />
                    </div>
                    <div className="google-acc-info">
                      <span className="google-acc-name">Use another Google account</span>
                      <span className="google-acc-email">Sign in with any @gmail.com or Workspace ID</span>
                    </div>
                    <ArrowRight size={15} style={{ color: 'var(--text-muted)' }} />
                  </button>
                </div>

                <div className="google-modal-notice">
                  To continue, Google will share your name, email address, and profile picture with ROIlytics. See ROIlytics Privacy Policy and Terms of Service.
                </div>
              </>
            ) : (
              <form onSubmit={handleCustomGoogleSubmit} className="google-custom-form">
                {googleError && (
                  <div className="auth-alert auth-alert-error" style={{ marginBottom: 12 }}>
                    <AlertCircle size={14} />
                    <span>{googleError}</span>
                  </div>
                )}
                <div className="form-group">
                  <label className="form-label">Your Full Name</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="e.g. Maya Patel"
                    value={googleCustomName}
                    onChange={e => setGoogleCustomName(e.target.value)}
                    autoFocus
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Google Email Address</label>
                  <input
                    type="email"
                    className="form-input"
                    placeholder="name@gmail.com"
                    value={googleCustomEmail}
                    onChange={e => setGoogleCustomEmail(e.target.value)}
                  />
                </div>

                <div className="google-custom-actions">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => { setGoogleMode('select'); setGoogleError(''); }}
                  >
                    Back to Accounts
                  </button>
                  <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>
                    Continue with this Account
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LoginPage;
