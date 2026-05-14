import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import CompanySelector from './components/CompanySelector';
import Dashboard from './components/Dashboard';
import ChatWidget from './components/ChatWidget';
import { companies } from './data/companies';
import './App.css';

function App() {
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [currentPage, setCurrentPage] = useState('Highlights and Takeaways');
  const [activeHighlightTab, setActiveHighlightTab] = useState('vendor_topics');
  const [isHighlightsExpanded, setIsHighlightsExpanded] = useState(false);

  const handleCompanySelect = (company) => {
    setSelectedCompany(company);
    setCurrentPage('Highlights and Takeaways');
  };

  const handleBack = () => {
    setSelectedCompany(null);
  };

  const handleNavigate = (page) => {
    // Toggle highlights expansion when clicking on Highlights (only if already on Highlights page)
    if (page === 'Highlights and Takeaways') {
      if (currentPage === 'Highlights and Takeaways') {
        // Already on Highlights page - toggle expansion
        setIsHighlightsExpanded(prev => !prev);
      } else {
        // Coming from another page - expand it
        setIsHighlightsExpanded(true);
      }
    } else {
      // Navigating away from Highlights - collapse
      setIsHighlightsExpanded(false);
    }
    setCurrentPage(page);
  };

  return (
    <div className="app-container">
      {!selectedCompany ? (
        <div className="selection-view">
          <CompanySelector companies={companies} onSelect={handleCompanySelect} />
        </div>
      ) : (
        <div className="dashboard-view">
          <Sidebar
            company={selectedCompany}
            currentPage={currentPage}
            onNavigate={handleNavigate}
            onBack={handleBack}
            activeHighlightTab={activeHighlightTab}
            setActiveHighlightTab={setActiveHighlightTab}
            isHighlightsExpanded={isHighlightsExpanded}
          />
          <main className="main-content">
            <Dashboard
              company={selectedCompany}
              currentPage={currentPage}
              activeHighlightTab={activeHighlightTab}
              setActiveHighlightTab={setActiveHighlightTab}
            />
          </main>

          {/* Chat Widget - Only show when company is selected */}
          <ChatWidget companyName={selectedCompany.name} />
        </div>
      )}
    </div>
  );
}

export default App;
