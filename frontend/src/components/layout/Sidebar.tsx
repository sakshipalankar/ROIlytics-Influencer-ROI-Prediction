import React from 'react';
import { useAppStore } from '../../store/useAppStore';
import {
  Search, BarChart3, Database, Bookmark, Star, X,
} from 'lucide-react';

const NAV_ITEMS = [
  { id: 'discover',  label: 'Discover',     icon: Search   },
  { id: 'shortlist', label: 'Shortlist',    icon: Bookmark },
  { id: 'analytics', label: 'Analytics',   icon: BarChart3},
  { id: 'explorer',  label: 'Data Explorer',icon: Database },
  { id: 'about',     label: 'About',        icon: Star     },
];

const Sidebar: React.FC = () => {
  const { activePage, setActivePage, shortlist, sidebarOpen, setSidebarOpen } = useAppStore();

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`sidebar${sidebarOpen ? ' open' : ' collapsed'}`}>
        {/* Close button (mobile) */}
        <button
          className="sidebar-close-btn"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close sidebar"
        >
          <X size={16} />
        </button>

        {/* Nav section */}
        <div className="nav-section-label">Platform</div>
        <nav>
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              id={`nav-${id}`}
              className={`nav-item${activePage === id ? ' active' : ''}`}
              onClick={() => { setActivePage(id); setSidebarOpen(false); }}
              style={{ width: '100%', textAlign: 'left' }}
              title={label}
            >
              <Icon className="nav-item-icon" size={18} />
              <span className="nav-item-label">{label}</span>
              {id === 'shortlist' && shortlist.length > 0 && (
                <span className="nav-badge">{shortlist.length}</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div style={{ fontSize: 11, marginBottom: 4, color: 'var(--text-muted)' }}>ROIlytics v3.0</div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>10,500 Influencer Profiles</div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
