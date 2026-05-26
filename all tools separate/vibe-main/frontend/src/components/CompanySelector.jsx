import React, { useState } from 'react';
import { ChevronDown, Plus, Trash2, X, Settings } from 'lucide-react';
import PromptSettingsModal from './PromptSettingsModal';
import './CompanySelector.css';

const CompanySelector = ({ companies, onSelect, onAdd, onDelete }) => {
    const [selectedCompany, setSelectedCompany] = useState('');
    const [isAdding, setIsAdding] = useState(false);
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [newName, setNewName] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (selectedCompany) {
            const company = companies.find(c => c.name === selectedCompany);
            if (company) {
                onSelect(company);
            }
        }
    };

    const handleAddVendor = (e) => {
        e.preventDefault();
        if (newName) {
            onAdd({
                name: newName,
                symbol: newName.slice(0, 4).toUpperCase(),
                sector: 'Custom'
            });
            setNewName('');
            setIsAdding(false);
        }
    };

    const handleDeleteVendor = (e, companyId) => {
        e.stopPropagation();
        if (window.confirm('Are you sure you want to delete this vendor?')) {
            onDelete(companyId);
            if (companies.find(c => c.id === companyId)?.name === selectedCompany) {
                setSelectedCompany('');
            }
        }
    };

    return (
        <div className="landing-page">
            {/* Header */}
            <header className="landing-header">
                <div className="header-content">
                    <div className="logo-section">
                        <span className="brand-name">NEGOTIATION ENGINE</span>
                    </div>
                </div>
            </header>

            {/* Split Screen Layout */}
            <div className="split-layout">
                {/* Left Side: Branding */}
                <section className="split-left">
                    <div className="hero-content">
                        <div className="hero-badge">AI-POWERED PLATFORM</div>
                        <h1 className="hero-title" style={{ color: "#ffffff" }}>
                            <span className="gradient-text">Strategic Vendor Intelligence</span>
                        </h1>
                        <p className="hero-subtitle">
                            Automate your quarterly business reviews, extract deep pricing insights, and prepare for critical vendor negotiations instantly.
                        </p>
                    </div>
                </section>

                {/* Right Side: Action Panel */}
                <section className="split-right">
                    <div className="selection-container">
                        {/* Selection Form */}
                        <form onSubmit={handleSubmit} className="selection-form">
                            <div className="form-group">
                                <div className="label-row">
                                    <label htmlFor="company-select" className="form-label">Select Vendor</label>
                                    <div className="action-buttons-row">
                                        <button 
                                            type="button" 
                                            className="settings-toggle-btn"
                                            onClick={() => setIsSettingsOpen(true)}
                                            title="Refine AI Prompts"
                                        >
                                            <Settings size={14} />
                                            Settings
                                        </button>
                                        <button 
                                            type="button" 
                                            className="add-toggle-btn"
                                            onClick={() => setIsAdding(!isAdding)}
                                        >
                                            {isAdding ? <X size={16} /> : <Plus size={16} />}
                                            {isAdding ? 'Cancel' : 'Add New'}
                                        </button>
                                    </div>
                                </div>
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
                                                {company.name}
                                            </option>
                                        ))}
                                    </select>
                                    <ChevronDown className="select-icon" size={20} />
                                </div>
                            </div>

                            <div className="button-group">
                                <button type="submit" className="analyze-btn" disabled={!selectedCompany}>
                                    View Briefing
                                </button>
                                {selectedCompany && (
                                    <button 
                                        type="button" 
                                        className="delete-btn"
                                        onClick={(e) => {
                                            const comp = companies.find(c => c.name === selectedCompany);
                                            if (comp) handleDeleteVendor(e, comp.id);
                                        }}
                                        title="Delete selected vendor"
                                    >
                                        <Trash2 size={20} />
                                    </button>
                                )}
                            </div>
                        </form>

                        {/* Add Vendor Form */}
                        {isAdding && (
                            <form onSubmit={handleAddVendor} className="add-vendor-form animate-slide-down">
                                <h3>Add New Vendor</h3>
                                <div className="input-group">
                                    <input 
                                        type="text" 
                                        placeholder="Company Name (e.g. Tesla)" 
                                        value={newName}
                                        onChange={(e) => setNewName(e.target.value)}
                                        required
                                    />
                                </div>
                                <p className="vendor-data-note">
                                    New vendors are added to the list first. Dashboard data will appear after vendor-specific files or live generation are available.
                                </p>
                                <button type="submit" className="submit-add-btn">
                                    Add to List
                                </button>
                            </form>
                        )}
                    </div>
                </section>
            </div>

            {/* Footer */}
            <footer className="landing-footer">
                <p>© 2026 Negotiation Engine• All rights reserved</p>
            </footer>

            {/* Prompt Settings Modal */}
            <PromptSettingsModal 
                isOpen={isSettingsOpen}
                onClose={() => setIsSettingsOpen(false)}
            />
        </div>
    );
};

export default CompanySelector;
