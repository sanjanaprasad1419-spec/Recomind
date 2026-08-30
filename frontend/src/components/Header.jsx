import React from 'react';
import { Search, Bell, HelpCircle, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Header() {
  return (
    <header className="top-header">
      <div className="search-bar">
        <Search size={16} style={{ color: 'var(--text-muted)' }} />
        <input type="text" placeholder="Search notes, stats..." />
      </div>

      <div className="header-actions">
        <button className="icon-btn" title="Help">
          <HelpCircle size={18} />
        </button>
        <button className="icon-btn" title="Notifications">
          <Bell size={18} />
        </button>
        <Link to="/upload" className="btn-new">
          <Plus size={16} /> New Upload
        </Link>
        <div className="user-avatar" title="User Profile">
          RM
        </div>
      </div>
    </header>
  );
}
