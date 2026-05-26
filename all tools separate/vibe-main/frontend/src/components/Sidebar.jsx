import React from 'react';
import {
  Sparkles,
  TrendingUp,
  Calendar,
  FileText,
  ArrowLeft,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import './Sidebar.css';

const Sidebar = ({ onNavigate, currentPage, onBack, company, activeHighlightTab, setActiveHighlightTab }) => {
  const highlightTabs = [
    { id: 'leadership', label: 'Leadership' },
    { id: 'vendor_topics', label: 'Vendor Discussion Topics' },
    { id: 'pricing_insights', label: 'Pricing Insights' },
    { id: 'products_features', label: 'Products and Features' },
    { id: 'ai_cloud_productivity', label: 'AI, Cloud and Productivity' }
  ];
  const menuItems = [
    { id: 'Highlights and Takeaways', icon: Sparkles, label: 'Highlights' },
    { id: 'Earnings', icon: TrendingUp, label: 'Earnings' },
    { id: 'Briefing Docs', icon: FileText, label: 'Briefing Docs' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo-area" onClick={onBack} style={{ cursor: 'pointer' }}>
          <ArrowLeft className="logo-icon" size={24} />
          <span className="logo-text">Back to Home</span>
        </div>
      </div>

      <div className="company-badge">
        <div className="company-icon">{company.symbol[0]}</div>
        <div className="company-info">
          <div className="company-symbol">{company.symbol}</div>
          <div className="company-name">{company.name}</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="nav-section">
          <h3 className="nav-title">Vendor Briefing Sections</h3>
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isHighlights = item.id === 'Highlights and Takeaways';
            const isActive = currentPage === item.id;

            return (
              <div key={item.id}>
                <button
                  onClick={() => onNavigate(item.id)}
                  className={`nav-item ${isActive ? 'active' : ''}`}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                </button>
              </div>
            );
          })}
        </div>
      </nav>
    </aside>
  );
};

export default Sidebar;
