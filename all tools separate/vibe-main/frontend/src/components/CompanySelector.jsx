import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import './CompanySelector.css';

const CompanySelector = ({ companies, onSelect }) => {
    const [selectedCompany, setSelectedCompany] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (selectedCompany) {
            const company = companies.find(c => c.name === selectedCompany);
            if (company) {
                onSelect(company);
            }
        }
    };

    return (
        <div className="landing-page">
            {/* Header */}
            <header className="landing-header">
                <div className="header-content">
                    <div className="logo-section">
                    </div>
                    <nav className="nav-links">
                    </nav>

                </div>
            </header>

            {/* Hero Section */}
            <section className="hero-section">
                <div className="hero-content">
                    <h1 className="hero-title">
                        <span className="gradient-text">Vendor Intelligence</span><br />
                    </h1>

                    {/* Selection Form */}
                    <form onSubmit={handleSubmit} className="selection-form">
                        <div className="form-group">
                            <label htmlFor="company-select" className="form-label">Vendor Intelligence</label>
                            <div className="select-wrapper">
                                <select
                                    id="company-select"
                                    value={selectedCompany}
                                    onChange={(e) => setSelectedCompany(e.target.value)}
                                    className="company-select"
                                    required
                                >
                                    <option value="">Choose a vendor...</option>
                                    {companies.map((company) => (
                                        <option key={company.id} value={company.name}>
                                            {company.name} ({company.symbol})
                                        </option>
                                    ))}
                                </select>
                                <ChevronDown className="select-icon" size={20} />
                            </div>
                        </div>

                        <button type="submit" className="analyze-btn" disabled={!selectedCompany}>
                            🚀 View Briefing
                        </button>
                    </form>
                </div>
            </section>

            {/* Footer */}
            <footer className="landing-footer">
                <p>Powered by Engineering Enterprise • © 2025 All rights reserved</p>
            </footer>
        </div>
    );
};

export default CompanySelector;
