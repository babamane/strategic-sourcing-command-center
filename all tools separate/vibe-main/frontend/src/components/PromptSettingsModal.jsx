import React, { useState, useEffect } from 'react';
import { X, Save, AlertTriangle, FileText, CheckCircle2, RefreshCw } from 'lucide-react';
import './PromptSettingsModal.css';

const PROMPT_TYPES = [
  {
    id: 'price_insight_prompt.txt',
    label: 'Pricing Insights',
    description: 'Guidelines for summarising verified vendor pricing updates, plan comparisons, and enterprise structures.',
    icon: 'DollarSign'
  },
  {
    id: 'vendor_topics_prompt.txt',
    label: 'Vendor Topics',
    description: 'Instructions on extracting major executive highlights and discussion topics from recent vendor communications.',
    icon: 'MessageSquare'
  },
  {
    id: 'product_features_prompt.txt',
    label: 'Products & Features',
    description: 'Rules for compiling product announcements, feature upgrades, and technical releases.',
    icon: 'Cpu'
  },
  {
    id: 'ai_cloud_productivity_prompt.txt',
    label: 'AI & Cloud Productivity',
    description: 'Prompts focusing on AI developments, cloud strategies, infrastructure, and productivity metrics.',
    icon: 'Cloud'
  }
];

const PromptSettingsModal = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState(PROMPT_TYPES[0].id);
  const [prompts, setPrompts] = useState({});
  const [editedPrompt, setEditedPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Fetch prompts on mount
  useEffect(() => {
    if (isOpen) {
      fetchPrompts();
    }
  }, [isOpen]);

  // Update editor content when tab changes or prompts are loaded
  useEffect(() => {
    if (prompts[activeTab] !== undefined) {
      setEditedPrompt(prompts[activeTab]);
    }
  }, [activeTab, prompts]);

  const fetchPrompts = async () => {
    setLoading(true);
    setError(null);
    try {
      // Backend runs on port 9001 during local dev
      const response = await fetch('http://localhost:9001/api/prompts');
      if (!response.ok) {
        throw new Error('Failed to fetch system prompts');
      }
      const data = await response.json();
      if (data.success) {
        setPrompts(data.prompts);
      } else {
        throw new Error(data.detail || 'Failed to load prompts');
      }
    } catch (err) {
      setError(err.message || 'Could not connect to backend server. Make sure the API is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaveSuccess(false);
    try {
      const response = await fetch('http://localhost:9001/api/prompts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          filename: activeTab,
          content: editedPrompt
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to save prompt changes');
      }

      const data = await response.json();
      if (data.success) {
        setPrompts(prev => ({
          ...prev,
          [activeTab]: editedPrompt
        }));
        setSaveSuccess(true);
        setTimeout(() => setSaveSuccess(false), 3000);
      } else {
        throw new Error(data.message || 'Failed to save prompt');
      }
    } catch (err) {
      setError(err.message || 'Failed to connect to backend server.');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="prompt-modal-overlay">
      <div className="prompt-modal-container">
        
        {/* Modal Header */}
        <header className="prompt-modal-header">
          <div className="header-title-wrapper">
            <span className="settings-badge">SYSTEM CONFIG</span>
            <h2>AI Prompt Engine Settings</h2>
            <p>Refine and customize system prompts dynamically to modify vendor intelligence outputs.</p>
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </header>

        {/* Modal Content Grid */}
        <div className="prompt-modal-body">
          
          {/* Sidebar Tabs */}
          <aside className="prompt-sidebar">
            <h3>PROMPT CATEGORIES</h3>
            <div className="tab-list">
              {PROMPT_TYPES.map((type) => {
                const isActive = activeTab === type.id;
                return (
                  <button
                    key={type.id}
                    className={`tab-item ${isActive ? 'active' : ''}`}
                    onClick={() => {
                      setActiveTab(type.id);
                      setSaveSuccess(false);
                    }}
                  >
                    <div className="tab-icon-wrapper">
                      <FileText size={16} />
                    </div>
                    <div className="tab-label-group">
                      <span className="tab-label">{type.label}</span>
                      <span className="tab-filename">{type.id}</span>
                    </div>
                  </button>
                );
              })}
            </div>
            
            <div className="sidebar-footer-tip">
              <AlertTriangle size={14} className="tip-icon" />
              <span>Editing these prompts affects the core reasoning and output structure generated by AI agents.</span>
            </div>
          </aside>

          {/* Main Editor Workspace */}
          <main className="prompt-workspace">
            {loading ? (
              <div className="workspace-loading">
                <RefreshCw className="spinner" size={32} />
                <p>Loading prompt configurations from server...</p>
              </div>
            ) : (
              <div className="editor-container">
                <div className="editor-meta">
                  <div className="meta-text">
                    <h3>{PROMPT_TYPES.find(t => t.id === activeTab)?.label} Prompt</h3>
                    <p>{PROMPT_TYPES.find(t => t.id === activeTab)?.description}</p>
                  </div>
                  
                  {/* Status Banner */}
                  <div className="editor-status-zone">
                    {saveSuccess && (
                      <span className="status-badge success animate-fade-in">
                        <CheckCircle2 size={14} /> Saved Successfully
                      </span>
                    )}
                    {error && (
                      <span className="status-badge error animate-fade-in">
                        <AlertTriangle size={14} /> Error
                      </span>
                    )}
                  </div>
                </div>

                {error && <div className="error-banner">{error}</div>}

                <div className="textarea-wrapper">
                  <textarea
                    value={editedPrompt}
                    onChange={(e) => setEditedPrompt(e.target.value)}
                    className="prompt-textarea"
                    placeholder="Enter customized prompt instructions..."
                    disabled={saving}
                  />
                </div>

                <div className="editor-actions">
                  <span className="char-count">
                    {(editedPrompt || '').length} characters
                  </span>
                  
                  <div className="action-buttons">
                    <button 
                      onClick={fetchPrompts} 
                      className="btn-secondary" 
                      disabled={saving || loading}
                      title="Reset / Reload current prompts from server"
                    >
                      <RefreshCw size={14} /> Reload
                    </button>
                    <button 
                      onClick={handleSave} 
                      className="btn-primary" 
                      disabled={saving || loading || editedPrompt === prompts[activeTab]}
                    >
                      {saving ? (
                        <>
                          <RefreshCw className="spinner" size={14} /> Saving...
                        </>
                      ) : (
                        <>
                          <Save size={14} /> Save & Apply Prompt
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
};

export default PromptSettingsModal;
