import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import CompanySelector from './components/CompanySelector';
import Dashboard from './components/Dashboard';
import ChatWidget from './components/ChatWidget';
import { companies as defaultCompanies } from './data/companies';
import './App.css';

function App() {
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [currentPage, setCurrentPage] = useState('Highlights and Takeaways');
  const [activeHighlightTab, setActiveHighlightTab] = useState('leadership');
  const [companiesList, setCompaniesList] = useState([]);

  // Load companies from localStorage or default
  useEffect(() => {
    const savedCompanies = localStorage.getItem('vibe_companies');
    if (savedCompanies) {
      try {
        setCompaniesList(JSON.parse(savedCompanies));
      } catch (e) {
        setCompaniesList(defaultCompanies);
      }
    } else {
      setCompaniesList(defaultCompanies);
    }
  }, []);

  // Save companies to localStorage
  useEffect(() => {
    if (companiesList.length > 0) {
      localStorage.setItem('vibe_companies', JSON.stringify(companiesList));
    }
  }, [companiesList]);

  const handleAddCompany = (newCompany) => {
    setCompaniesList(prev => [...prev, { ...newCompany, id: newCompany.name.toLowerCase().replace(/\s+/g, '-') }]);
  };

  const handleDeleteCompany = (companyId) => {
    setCompaniesList(prev => prev.filter(c => c.id !== companyId));
  };

  const handleCompanySelect = (company) => {
    setSelectedCompany(company);
    setCurrentPage('Highlights and Takeaways');
  };

  const handleBack = () => {
    setSelectedCompany(null);
  };

  const handleNavigate = (page) => {
    setCurrentPage(page);
  };

  return (
    <div className="app-container">
      {!selectedCompany ? (
        <div className="selection-view">
          <CompanySelector 
            companies={companiesList} 
            onSelect={handleCompanySelect}
            onAdd={handleAddCompany}
            onDelete={handleDeleteCompany}
          />
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
