import React, { useState, useRef, useEffect } from 'react';
import { useAppStore, pickColor } from '../../store/useAppStore';
import { Menu, TrendingUp, LogOut, User, ChevronDown, Bookmark } from 'lucide-react';

const TopNavbar: React.FC = () => {
  const { user, logout, toggleSidebar, sidebarOpen, shortlist, setActivePage, activePage } = useAppStore();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropRef.current && !dropRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const avatarColor = user ? pickColor(user.username) : '#6366f1';
  const initials = user
    ? user.username.slice(0, 2).toUpperCase()
    : '??';

  const joinDate = user
    ? new Date(user.joinedAt).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
    : '';

  return (
    <header className="top-navbar">
      {/* Left: Hamburger + Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <button
          id="hamburger-btn"
          className="hamburger-btn"
          onClick={toggleSidebar}
          aria-label="Toggle sidebar"
          title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
        >
          <Menu size={20} />
        </button>

        <div className="navbar-logo">
          <div className="navbar-logo-icon">
            <TrendingUp size={16} color="white" />
          </div>
          <span className="navbar-logo-text">ROIlytics</span>
        </div>
      </div>

      {/* Center: Quick nav pills */}
      <nav className="navbar-quick-nav">
        {[
          { id: 'discover',  label: '🔍 Discover' },
          { id: 'shortlist', label: `📌 Shortlist${shortlist.length > 0 ? ` (${shortlist.length})` : ''}` },
          { id: 'analytics', label: '📊 Analytics' },
        ].map(item => (
          <button
            key={item.id}
            className={`navbar-nav-pill${activePage === item.id ? ' active' : ''}`}
            onClick={() => setActivePage(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>

      {/* Right: User Profile */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }} ref={dropRef}>
        {/* Shortlist quick-access */}
        {shortlist.length > 0 && (
          <button
            className="navbar-icon-btn"
            onClick={() => setActivePage('shortlist')}
            title="View shortlist"
          >
            <Bookmark size={18} />
            <span className="navbar-badge">{shortlist.length}</span>
          </button>
        )}

        {/* User avatar button */}
        <button
          id="user-menu-btn"
          className="user-avatar-btn"
          onClick={() => setDropdownOpen(p => !p)}
          style={{ '--avatar-color': avatarColor } as React.CSSProperties}
        >
          <div className="user-avatar" style={{ background: avatarColor }}>
            {initials}
          </div>
          <div className="user-info-text">
            <span className="user-name">{user?.username}</span>
            <span className="user-email">{user?.email}</span>
          </div>
          <ChevronDown size={14} style={{
            color: 'var(--text-muted)',
            transform: dropdownOpen ? 'rotate(180deg)' : 'none',
            transition: 'transform 0.2s',
          }} />
        </button>

        {/* Dropdown */}
        {dropdownOpen && (
          <div className="user-dropdown animate-scale-in">
            {/* Profile header */}
            <div className="user-dropdown-header">
              <div className="user-avatar-lg" style={{ background: avatarColor }}>
                {initials}
              </div>
              <div>
                <div style={{ fontWeight: 800, fontSize: 15, color: 'var(--text-primary)' }}>
                  {user?.username}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{user?.email}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                  Member since {joinDate}
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="user-dropdown-stats">
              <div className="ud-stat">
                <span className="ud-stat-value">{shortlist.length}</span>
                <span className="ud-stat-label">Shortlisted</span>
              </div>
              <div className="ud-stat-divider" />
              <div className="ud-stat">
                <span className="ud-stat-value">10.5K</span>
                <span className="ud-stat-label">Profiles</span>
              </div>
              <div className="ud-stat-divider" />
              <div className="ud-stat">
                <span className="ud-stat-value">10</span>
                <span className="ud-stat-label">Categories</span>
              </div>
            </div>

            <div className="user-dropdown-divider" />

            {/* Menu items */}
            <button
              className="user-dropdown-item"
              onClick={() => { setActivePage('about'); setDropdownOpen(false); }}
            >
              <User size={15} />
              <span>Profile & Settings</span>
            </button>

            <button
              className="user-dropdown-item"
              onClick={() => { setActivePage('shortlist'); setDropdownOpen(false); }}
            >
              <Bookmark size={15} />
              <span>My Shortlist{shortlist.length > 0 && ` (${shortlist.length})`}</span>
            </button>

            <div className="user-dropdown-divider" />

            <button
              id="logout-btn"
              className="user-dropdown-item danger"
              onClick={() => { logout(); setDropdownOpen(false); }}
            >
              <LogOut size={15} />
              <span>Sign Out</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

export default TopNavbar;
