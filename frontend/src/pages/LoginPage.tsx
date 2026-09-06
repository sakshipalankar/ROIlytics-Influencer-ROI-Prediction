import React, { useState } from 'react';
import { useAppStore, pickColor } from '../store/useAppStore';
import { TrendingUp, Eye, EyeOff, CheckCircle, AlertCircle, Sun, Moon } from 'lucide-react';

/* ── Simple local "auth" — stores in zustand/localStorage ── */

const FAKE_DB_KEY = 'roilytics-users';

interface StoredUser { username: string; email: string; password: string }

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

  const fillDemo = (e: string, p: string) => {
    setEmail(e);
    setPassword(p);
    setError('');
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

      {/* Left panel — branding */}
      <div className="auth-left">
        <div className="auth-brand">
          <div className="auth-logo">
            <TrendingUp size={28} color="var(--bg-base)" />
          </div>
          <h1 className="auth-brand-name">ROIlytics</h1>
        </div>

        <div className="auth-hero-text">
          <h2>Find your perfect<br />influencer match</h2>
          <p>
            AI-powered influencer discovery platform. Search 10,500+ profiles,
            score them by fit, and predict campaign ROI — all in seconds.
          </p>
        </div>

        <div className="auth-stats-row">
          {[
            { value: '10,500+', label: 'Influencer Profiles' },
            { value: '10',      label: 'Categories' },
            { value: '17',      label: 'Countries' },
          ].map(s => (
            <div className="auth-stat" key={s.label}>
              <div className="auth-stat-value">{s.value}</div>
              <div className="auth-stat-label">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Decorative influencer cards */}
        <div className="auth-deco-cards">
          {[
            { name: '@fitness_guru_',  score: 94, tier: 'Micro', er: '7.2%', color: '#10b981' },
            { name: '@tech_visionary', score: 87, tier: 'Macro', er: '4.1%', color: 'var(--accent-primary)' },
            { name: '@beauty.world',   score: 81, tier: 'Nano',  er: '9.8%', color: '#f43f5e' },
          ].map((c, i) => (
            <div className="auth-deco-card" key={c.name} style={{ animationDelay: `${i * 0.15}s` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: '50%',
                  background: c.color, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 14, fontWeight: 800, color: 'var(--bg-base)',
                }}>
                  {c.name[1].toUpperCase()}
                </div>
                <div>
                  <div className="auth-deco-name">{c.name}</div>
                  <div className="auth-deco-meta">{c.tier} · ER {c.er}</div>
                </div>
              </div>
              <div className="auth-deco-score" style={{
                background: c.color + '22',
                color: c.color,
                border: `1px solid ${c.color}55`,
              }}>
                {c.score}/100
              </div>
            </div>
          ))}
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

              {/* Demo quick-login chips */}
              <div className="demo-chips">
                <span className="demo-chip-label">⚡ Quick Fill:</span>
                <button
                  type="button"
                  className="demo-chip"
                  onClick={() => fillDemo('demo@roilytics.ai', 'Password123!')}
                >
                  Demo Account
                </button>
                <button
                  type="button"
                  className="demo-chip"
                  onClick={() => fillDemo('sarah.chen@glowbeauty.com', 'Password123!')}
                >
                  Sarah (Brand Mgr)
                </button>
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
        </div>

        <p className="auth-footer-note">
          ROIlytics · Influencer Discovery Platform · v3.0
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
