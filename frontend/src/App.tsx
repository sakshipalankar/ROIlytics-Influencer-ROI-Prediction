import React from 'react';
import Sidebar from './components/layout/Sidebar';
import TopNavbar from './components/layout/TopNavbar';
import LoginPage from './pages/LoginPage';
import Discover from './pages/Discover';
import Shortlist from './pages/Shortlist';
import Analytics from './pages/Analytics';
import Explorer from './pages/Explorer';
import About from './pages/About';
import { useAppStore } from './store/useAppStore';

const PAGE_MAP: Record<string, React.FC> = {
  discover:  Discover,
  shortlist: Shortlist,
  analytics: Analytics,
  explorer:  Explorer,
  about:     About,
};

const App: React.FC = () => {
  const { user, activePage, sidebarOpen } = useAppStore();

  // ── Auth gate ──────────────────────────────────────────────────────────────
  if (!user) return <LoginPage />;

  const PageComponent = PAGE_MAP[activePage] ?? Discover;

  return (
    <div className="app-root">
      {/* Top Navbar — always visible when logged in */}
      <TopNavbar />

      <div className={`app-body${sidebarOpen ? '' : ' sidebar-collapsed'}`}>
        <Sidebar />
        <main className="main-content">
          <PageComponent />
        </main>
      </div>
    </div>
  );
};

export default App;
