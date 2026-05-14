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

const Sidebar = ({ onNavigate, currentPage, onBack, company, activeHighlightTab, setActiveHighlightTab, isHighlightsExpanded }) => {
  const highlightTabs = [
    { id: 'vendor_topics', label: 'Vendor Discussion Topics' },
    { id: 'pricing_insights', label: 'Pricing Insights' },
    { id: 'products_features', label: 'Products and Features' },
    { id: 'ai_cloud_productivity', label: 'AI, Cloud and Productivity' },
    { id: 'meta_synergies', label: 'Vendor Synergies' },
    { id: 'meta_spend_metrics', label: 'Vendor Spend and Metrics' }
  ];
  const menuItems = [
    { id: 'Highlights and Takeaways', icon: Sparkles, label: 'Highlights' },
    { id: 'Earnings', icon: TrendingUp, label: 'Earnings' },
    { id: 'QBR', icon: Calendar, label: 'QBR' },
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
            const showDropdown = isHighlights && isActive && isHighlightsExpanded;

            return (
              <div key={item.id}>
                <button
                  onClick={() => onNavigate(item.id)}
                  className={`nav-item ${isActive ? 'active' : ''}`}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                  {isHighlights && isActive && (
                    <span className="nav-item-chevron">
                      {isHighlightsExpanded ? (
                        <ChevronDown size={16} />
                      ) : (
                        <ChevronRight size={16} />
                      )}
                    </span>
                  )}
                </button>
                {showDropdown && (
                  <div className="highlights-dropdown-wrapper">
                    <select
                      className="highlights-dropdown"
                      value={activeHighlightTab}
                      onChange={(e) => setActiveHighlightTab(e.target.value)}
                    >
                      {highlightTabs.map(tab => (
                        <option key={tab.id} value={tab.id}>
                          {tab.label}
                        </option>
                      ))}
                    </select>
                    <ChevronDown className="dropdown-icon" size={18} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </nav>
    </aside>
  );
};

export default Sidebar;
