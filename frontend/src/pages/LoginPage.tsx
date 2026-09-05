import React, { useState } from 'react';
import { useAppStore, pickColor } from '../store/useAppStore';
import { TrendingUp, Eye, EyeOff, CheckCircle, AlertCircle } from 'lucide-react';

/* ── Simple local "auth" — stores in zustand/localStorage ── */

const FAKE_DB_KEY = 'roilytics-users';

interface StoredUser { username: string; email: string; password: string }

const getUsers = (): StoredUser[] => {
  try { return JSON.parse(localStorage.getItem(FAKE_DB_KEY) || '[]'); }
  catch { return []; }
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
  const { setUser } = useAppStore();
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

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(''); setSuccess('');
    if (!email || !password) { setError('Please fill in all fields.'); return; }
    if (!validateEmail(email)) { setError('Invalid email address.'); return; }

    setLoading(true);
    await new Promise(r => setTimeout(r, 700)); // simulate network

    const users = getUsers();
    const found = users.find(u => u.email === email && u.password === password);
    if (!found) {
      setLoading(false);
      setError('Incorrect email or password.');
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
      {/* Left panel — branding */}
      <div className="auth-left">
        <div className="auth-brand">
          <div className="auth-logo">
            <TrendingUp size={28} color="white" />
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

        {/* Decorative cards */}
        <div className="auth-deco-cards">
          {[
            { name: '@fitness_guru_',  score: 94, tier: 'Micro', er: '7.2%', color: '#10b981' },
            { name: '@tech_visionary', score: 87, tier: 'Macro', er: '4.1%', color: '#6366f1' },
            { name: '@beauty.world',   score: 81, tier: 'Nano',  er: '9.8%', color: '#f43f5e' },
          ].map((c, i) => (
            <div className="auth-deco-card" key={c.name} style={{ animationDelay: `${i * 0.15}s` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: '50%',
                  background: c.color, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 14, fontWeight: 800, color: 'white',
                }}>
                  {c.name[1].toUpperCase()}
                </div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 13, color: '#f1f5f9' }}>{c.name}</div>
                  <div style={{ fontSize: 11, color: '#94a3b8' }}>{c.tier} · ER {c.er}</div>
                </div>
              </div>
              <div style={{
                background: c.color + '22', color: c.color,
                border: `1px solid ${c.color}55`,
                borderRadius: 8, padding: '3px 10px',
                fontSize: 12, fontWeight: 800,
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
                          background: i < strength.score ? strength.color : 'rgba(255,255,255,0.08)',
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

        <p style={{ textAlign: 'center', fontSize: 12, color: '#475569', marginTop: 24 }}>
          ROIlytics · Influencer Discovery Platform · v3.0
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
