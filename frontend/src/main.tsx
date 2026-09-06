import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// ── Pre-hydration theme sync (avoids flash of wrong theme) ────────────────────
try {
  const stored = localStorage.getItem('roilytics-store');
  if (stored) {
    const parsed = JSON.parse(stored);
    const theme = parsed?.state?.theme ?? 'dark';
    document.documentElement.setAttribute('data-theme', theme);
  } else {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
} catch { document.documentElement.setAttribute('data-theme', 'dark'); }

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

