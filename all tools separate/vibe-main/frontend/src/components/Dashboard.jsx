import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, AreaChart, Area, Tooltip, XAxis, YAxis } from 'recharts';
import { Download, Share2, Info } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './Dashboard.css';

const API_URL = '';

const Dashboard = ({ company, currentPage, activeHighlightTab, setActiveHighlightTab }) => {
    const [summary, setSummary] = useState('');
    const [stockData, setStockData] = useState(null);
    const [metrics, setMetrics] = useState(null);
    const [chartData, setChartData] = useState([]);
    const [isLoadingSummary, setIsLoadingSummary] = useState(false);
    const [isLoadingStock, setIsLoadingStock] = useState(false);
    const [isLoadingEarnings, setIsLoadingEarnings] = useState(false);
    const [error, setError] = useState(null);
    const [stockError, setStockError] = useState(null);
    const [timeRange, setTimeRange] = useState('1mo');
    const [earningsData, setEarningsData] = useState(null);
    const [highlightsData, setHighlightsData] = useState({});
    const [highlightsSources, setHighlightsSources] = useState({});
    const [isLoadingHighlights, setIsLoadingHighlights] = useState(false);
    const [qbrData, setQbrData] = useState(null);
    const [isLoadingQbr, setIsLoadingQbr] = useState(false);
    const [briefingData, setBriefingData] = useState(null);
    const [isLoadingBriefing, setIsLoadingBriefing] = useState(false);
    const [showSources, setShowSources] = useState(false);
    const highlightTabs = [
        { id: 'vendor_topics', label: 'Vendor Discussion Topics' },
        { id: 'pricing_insights', label: 'Pricing Insights' },
        { id: 'products_features', label: 'Products and Features' },
        { id: 'ai_cloud_productivity', label: 'AI, Cloud and Productivity' },
        { id: 'meta_synergies', label: 'Vendor Synergies' },
        { id: 'meta_spend_metrics', label: 'Vendor Spend and Metrics' }
    ];

    // Clear data when company changes
    useEffect(() => {
        if (company) {
            setHighlightsData({});
            setHighlightsSources({});
            setQbrData(null);
            setBriefingData(null);
            setEarningsData(null);
            setSummary('');
            setStockData(null);
            setMetrics(null);
            setChartData([]);
        }
    }, [company]);

    useEffect(() => {
        if (!company) return;

        const fetchSummary = async () => {
            setIsLoadingSummary(true);
            try {
                const res = await fetch(`${API_URL}/summary`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ company_name: company.name })
                });
                if (res.ok) {
                    const data = await res.json();
                    setSummary(data.summary);
                } else {
                    setSummary("Unable to generate summary at this time.");
                }
            } catch (err) {
                console.error("Summary fetch error:", err);
                setSummary("Error connecting to summary service.");
            } finally {
                setIsLoadingSummary(false);
            }
        };

        const fetchStock = async () => {
            setIsLoadingStock(true);
            setStockError(null);
            setStockData(null);
            try {
                const res = await fetch(`${API_URL}/stock-data`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ company_name: company.name })
                });
                if (res.ok) {
                    const data = await res.json();
                    // Check if data is valid
                    if (data && data.realtime_price && data.historical_data) {
                        setStockData(data);
                        updateChartData(data, timeRange);
                    } else {
                        setStockError("Company does not have stock data or is delisted from stock exchange");
                    }
                } else {
                    setStockError("Company does not have stock data or is delisted from stock exchange");
                }
            } catch (err) {
                console.error("Stock fetch error:", err);
                setStockError("Company does not have stock data or is delisted from stock exchange");
            } finally {
                setIsLoadingStock(false);
            }
        };

        const fetchMetrics = async () => {
            try {
                const res = await fetch(`${API_URL}/company-metrics`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ company_name: company.name })
                });
                if (res.ok) {
                    const data = await res.json();
                    setMetrics(data);
                }
            } catch (err) {
                console.error("Metrics fetch error:", err);
            }
        };

        const fetchEarnings = async () => {
            setIsLoadingEarnings(true);
            try {
                const res = await fetch(`${API_URL}/earnings`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ company_name: company.name })
                });
                if (res.ok) {
                    const data = await res.json();
                    setEarningsData(data.earnings);
                } else {
                    console.error("Failed to fetch earnings");
                }
            } catch (err) {
                console.error("Earnings fetch error:", err);
            } finally {
                setIsLoadingEarnings(false);
            }
        };

        // Only fetch summary if we are on the Full Summary page
        if (currentPage === 'Full Summary' && !summary) {
            fetchSummary();
        }

        // Fetch stock and metrics for both Highlights and Summary
        if (currentPage === 'Highlights and Takeaways' || currentPage === 'Full Summary') {
            if (!stockData) fetchStock();
            if (!metrics) fetchMetrics();
        }

        // Fetch earnings if on Earnings page
        if (currentPage === 'Earnings' && !earningsData) {
            fetchEarnings();
        }

    }, [company, currentPage, summary, stockData, metrics, earningsData]);

    const updateChartData = (data, range) => {
        if (data && data.historical_data && data.historical_data[range]) {
            const processed = data.historical_data[range].map(item => ({
                date: item.date,
                price: item.close
            }));
            setChartData(processed);
        }
    };

    const handleTimeRangeChange = (range) => {
        setTimeRange(range);
        if (stockData) {
            updateChartData(stockData, range);
        }
    };

    const fetchHighlights = async (tabId) => {
        if (!company) return;

        setIsLoadingHighlights(true);
        try {
            const res = await fetch(`${API_URL}/highlights`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    company_name: company.name,
                    tab: tabId
                })
            });
            if (res.ok) {
                const result = await res.json();

                // Check if the response is JSON with sources (for pricing_insights, products_features, etc.)
                let content = result.data.content;
                let sources = [];

                try {
                    const parsed = JSON.parse(content);
                    if (parsed.content && parsed.sources) {
                        content = parsed.content;
                        sources = parsed.sources;
                        console.log(`[${tabId}] Parsed sources:`, sources);
                    }
                } catch (e) {
                    // Not JSON, use as-is (for other tabs)
                    console.log(`[${tabId}] Not JSON format, using as-is`);
                }

                setHighlightsData(prev => ({
                    ...prev,
                    [tabId]: content
                }));

                setHighlightsSources(prev => ({
                    ...prev,
                    [tabId]: sources
                }));
            } else {
                console.error("Failed to fetch highlights");
            }
        } catch (err) {
            console.error("Highlights fetch error:", err);
        } finally {
            setIsLoadingHighlights(false);
        }
    };

    // Fetch highlights when tab changes
    useEffect(() => {
        if (currentPage === 'Highlights and Takeaways' && company) {
            if (!highlightsData[activeHighlightTab]) {
                fetchHighlights(activeHighlightTab);
            }
        }
    }, [activeHighlightTab, company, currentPage, highlightsData]);

    const fetchQbr = async () => {
        if (!company) return;

        setIsLoadingQbr(true);
        try {
            const res = await fetch(`${API_URL}/qbr`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    company_name: company.name
                })
            });
            if (res.ok) {
                const result = await res.json();
                setQbrData(result.qbr);
            } else {
                console.error("Failed to fetch QBR");
            }
        } catch (err) {
            console.error("QBR fetch error:", err);
        } finally {
            setIsLoadingQbr(false);
        }
    };

    // Fetch QBR when page changes
    useEffect(() => {
        if (currentPage === 'QBR' && company && !qbrData) {
            fetchQbr();
        }
    }, [company, currentPage, qbrData]);

    const fetchBriefing = async () => {
        if (!company) return;

        setIsLoadingBriefing(true);
        try {
            const res = await fetch(`${API_URL}/briefing`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    company_name: company.name
                })
            });
            if (res.ok) {
                const result = await res.json();
                setBriefingData(result.briefing);
            } else {
                console.error("Failed to fetch Briefing");
            }
        } catch (err) {
            console.error("Briefing fetch error:", err);
        } finally {
            setIsLoadingBriefing(false);
        }
    };

    // Fetch Briefing when page changes
    useEffect(() => {
        if (currentPage === 'Briefing Docs' && company && !briefingData) {
            fetchBriefing();
        }
    }, [company, currentPage, briefingData]);

    const handleExport = () => {
        let content = '';
        let title = '';

        // Improved Markdown to HTML converter for Word
        const formatForDoc = (text) => {
            if (!text) return '';

            // 1. Split into lines
            const lines = text.split('\n');
            let html = '';
            let inList = false;

            lines.forEach(line => {
                const trimmed = line.trim();

                // Headings
                if (line.startsWith('# ')) {
                    if (inList) { html += '</ul>'; inList = false; }
                    html += `<h1>${line.substring(2)}</h1>`;
                } else if (line.startsWith('## ')) {
                    if (inList) { html += '</ul>'; inList = false; }
                    html += `<h2>${line.substring(3)}</h2>`;
                } else if (line.startsWith('### ')) {
                    if (inList) { html += '</ul>'; inList = false; }
                    html += `<h3>${line.substring(4)}</h3>`;
                }
                // Lists (Bullet points)
                else if (line.startsWith('- ') || line.startsWith('* ') || line.startsWith('• ')) {
                    if (!inList) {
                        html += '<ul>';
                        inList = true;
                    }
                    // Bold formatting inside list items
                    let itemText = line.substring(2).replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
                    html += `<li>${itemText}</li>`;
                }
                // Empty lines / Paragraph breaks
                else if (trimmed === '') {
                    if (inList) { html += '</ul>'; inList = false; }
                }
                // Standard Text (Paragraphs)
                else {
                    if (inList) { html += '</ul>'; inList = false; }
                    // Bold formatting inside paragraphs
                    let paraText = line.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
                    html += `<p>${paraText}</p>`;
                }
            });

            if (inList) { html += '</ul>'; }
            return html;
        };

        if (currentPage === 'Highlights and Takeaways') {
            const activeTabLabel = highlightTabs.find(t => t.id === activeHighlightTab)?.label;
            const tabContent = highlightsData[activeHighlightTab] || 'No data available.';
            title = `${company.name} - ${activeTabLabel}`;
            content = `<h1>${title}</h1>${formatForDoc(tabContent)}`;
        } else if (currentPage === 'QBR') {
            title = `${company.name} - Quarterly Business Review`;
            content = `<h1>${title}</h1>${formatForDoc(qbrData?.content || 'No QBR data available.')}`;
        } else if (currentPage === 'Briefing Docs') {
            title = `${company.name} - Vendor Briefing Document`;
            content = `<h1>${title}</h1>${formatForDoc(briefingData?.content || 'No Briefing data available.')}`;
        } else if (currentPage === 'Earnings') {
            title = `${company.name} - Earnings Summary`;
            const summary = earningsData?.summary || 'No summary available.';
            content = `<h1>${title}</h1>${formatForDoc(summary)}`;
        } else {
            content = `<p>Export for ${currentPage} not supported yet.</p>`;
        }

        const htmlContent = `
            <!DOCTYPE html>
            <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
            <head>
                <meta charset='utf-8'>
                <title>${title}</title>
                <!--[if gte mso 9]>
                <xml>
                <w:WordDocument>
                    <w:View>Print</w:View>
                    <w:Zoom>100</w:Zoom>
                    <w:DoNotOptimizeForBrowser/>
                </w:WordDocument>
                </xml>
                <![endif]-->
                <style>
                    body { font-family: 'Arial', sans-serif; font-size: 11pt; line-height: 1.5; color: #333; }
                    h1 { font-size: 24pt; color: #1a73e8; border-bottom: 2px solid #ddd; padding-bottom: 15px; margin-bottom: 25px; margin-top: 0; }
                    h2 { font-size: 16pt; color: #1a73e8; margin-top: 25px; margin-bottom: 12px; }
                    h3 { font-size: 13pt; color: #444; font-weight: bold; margin-top: 20px; margin-bottom: 10px; }
                    p { margin-bottom: 12px; text-align: justify; }
                    ul { margin-bottom: 15px; margin-top: 5px; padding-left: 30px; }
                    li { margin-bottom: 5px; }
                    b { color: #222; }
                </style>
            </head>
            <body>
                ${content}
            </body>
            </html>
        `;

        const blob = new Blob([htmlContent], { type: 'application/msword' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}.doc`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    const renderContent = () => {
        // Highlights and Takeaways Page
        if (currentPage === 'Highlights and Takeaways') {
            const currentSources = highlightsSources[activeHighlightTab] || [];

            return (
                <div className="highlights-container">
                    <div className="highlight-content">
                        {isLoadingHighlights ? (
                            <div className="loading-state">
                                <div className="spinner"></div>
                                <p>Loading highlights...</p>
                            </div>
                        ) : highlightsData[activeHighlightTab] ? (
                            <div className="highlights-data-card">
                                <div className="highlights-header">
                                    <h3>{highlightTabs.find(t => t.id === activeHighlightTab)?.label}</h3>
                                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                        <span className="ai-badge">AI Generated</span>
                                        {currentSources.length > 0 && (
                                            <button
                                                className="info-btn"
                                                onClick={() => setShowSources(true)}
                                                title="View Sources"
                                            >
                                                <Info size={16} />
                                            </button>
                                        )}
                                    </div>
                                </div>
                                <div className="highlights-text">
                                    <ReactMarkdown>{highlightsData[activeHighlightTab]}</ReactMarkdown>
                                </div>
                            </div>
                        ) : (
                            <div className="placeholder-content">
                                <h3>{highlightTabs.find(t => t.id === activeHighlightTab)?.label}</h3>
                                <p>No data available for this section.</p>
                            </div>
                        )}
                    </div>

                    {/* Sources Modal */}
                    {showSources && currentSources.length > 0 && (
                        <div className="sources-modal-overlay" onClick={() => setShowSources(false)}>
                            <div className="sources-modal" onClick={(e) => e.stopPropagation()}>
                                <div className="sources-modal-header">
                                    <h3>Sources</h3>
                                    <button className="close-btn" onClick={() => setShowSources(false)}>×</button>
                                </div>
                                <div className="sources-modal-content">
                                    {currentSources.map((source, idx) => (
                                        <div key={idx} className="source-item">
                                            <div className="source-number">{idx + 1}</div>
                                            <div className="source-details">
                                                <a href={source.url} target="_blank" rel="noopener noreferrer" className="source-title">
                                                    {source.title}
                                                </a>
                                                <div className="source-meta">
                                                    <span className="source-date">{source.date}</span>
                                                    <span className="source-url">{new URL(source.url).hostname}</span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            );
        }

        // QBR Page
        if (currentPage === 'QBR') {
            if (isLoadingQbr) {
                return (
                    <div className="loading-state">
                        <div className="spinner"></div>
                        <p>Generating Quarterly Business Review...</p>
                        <span className="loading-subtext">Optimizing report based on latest data</span>
                    </div>
                );
            }

            if (qbrData) {
                return (
                    <div className="highlights-data-card">
                        <div className="highlights-header">
                            <h3>Quarterly Business Review</h3>
                            <span className="ai-badge">AI Generated</span>
                        </div>
                        <div className="highlights-text">
                            <ReactMarkdown>{qbrData.content}</ReactMarkdown>
                        </div>
                    </div>
                );
            }

            return (
                <div className="placeholder-content">
                    <h3>Quarterly Business Review</h3>
                    <p>Select a company to generate report.</p>
                </div>
            );
        }

        // Briefing Docs Page
        if (currentPage === 'Briefing Docs') {
            if (isLoadingBriefing) {
                return (
                    <div className="loading-state">
                        <div className="spinner"></div>
                        <p>Generating Vendor Briefing Document...</p>
                        <span className="loading-subtext">Analyzing context, risks, and negotiation strategy</span>
                    </div>
                );
            }

            if (briefingData) {
                return (
                    <div className="highlights-data-card">
                        <div className="highlights-header">
                            <h3>Vendor Briefing Document</h3>
                            <span className="ai-badge">AI Generated</span>
                        </div>
                        <div className="highlights-text">
                            <ReactMarkdown>{briefingData.content}</ReactMarkdown>
                        </div>
                    </div>
                );
            }

            return (
                <div className="placeholder-content">
                    <h3>Vendor Briefing Document</h3>
                    <p>Select a company to generate briefing doc.</p>
                </div>
            );
        }

        // Earnings page
        if (currentPage === 'Earnings') {
            if (isLoadingEarnings) {
                return (
                    <div className="loading-state">
                        <div className="spinner"></div>
                        <p>Fetching earnings data...</p>
                        <span className="loading-subtext">This may take a few moments</span>
                    </div>
                );
            }

            if (earningsData) {
                return (
                    <div className="earnings-container">
                        <div className="metrics-card-styled">
                            <h3>Earnings Metric</h3>
                            <div className="metrics-list">
                                <div className="metric-row">
                                    <span className="metric-label">Announce Date</span>
                                    <span className="metric-value">{earningsData.announce_date}</span>
                                </div>
                                <div className="metric-row">
                                    <span className="metric-label">EPS Estimated</span>
                                    <span className="metric-value">{earningsData.eps_estimated}</span>
                                </div>
                                <div className="metric-row">
                                    <span className="metric-label">EPS Actual</span>
                                    <span className="metric-value">{earningsData.eps_actual}</span>
                                </div>
                                <div className="metric-row">
                                    <span className="metric-label">EPS Surprise (%)</span>
                                    <span className={`metric-value ${earningsData.eps_surprise_percent?.includes('Beat') ? 'text-green' : ''}`}>
                                        {earningsData.eps_surprise_percent}
                                    </span>
                                </div>
                                <div className="metric-row">
                                    <span className="metric-label">Revenue Actual</span>
                                    <span className="metric-value">{earningsData.revenue_actual}</span>
                                </div>
                                <div className="metric-row">
                                    <span className="metric-label">Revenue Surprise</span>
                                    <span className={`metric-value ${earningsData.revenue_surprise?.includes('Beat') ? 'text-green' : ''}`}>
                                        {earningsData.revenue_surprise}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {earningsData.summary && (
                            <div className="earnings-summary-card">
                                <div className="summary-header">
                                    <h3>Earnings Overview</h3>
                                    <span className="ai-badge">AI Analysis</span>
                                </div>
                                <div className="summary-content-text">
                                    <ReactMarkdown>{earningsData.summary}</ReactMarkdown>
                                </div>
                            </div>
                        )}
                    </div>
                );
            }

            // No earnings data available
            return (
                <div className="coming-soon">
                    <h3>Earnings Data</h3>
                    <p>No earnings data available.</p>
                </div>
            );
        }

        // Full Summary Page (Original Markdown Summary)
        if (currentPage === 'Full Summary') {
            if (isLoadingSummary) {
                return (
                    <div className="loading-state">
                        <div className="spinner"></div>
                        <p>Analyzing earnings call transcript with AI...</p>
                        <span className="loading-subtext">This may take a few moments</span>
                    </div>
                );
            }

            return (
                <div className="markdown-content">
                    <ReactMarkdown>{summary}</ReactMarkdown>
                </div>
            );
        }

        // Other pages (QBR, Briefing Docs, Spend)
        return (
            <div className="coming-soon">
                <h3>{currentPage}</h3>
                <p>This module is currently under development.</p>
            </div>
        );
    };

    return (
        <div className="dashboard-container">
            <header className="dashboard-header">
                <div>
                    <h1 className="page-title">{currentPage}</h1>
                    <p className="page-subtitle">Latest Earnings Report • {company.name}</p>
                </div>
                <div className="header-actions">
                    <button className="action-btn" onClick={handleExport}><Download size={18} /> Export</button>
                    <button className="action-btn"><Share2 size={18} /> Share</button>
                </div>
            </header>

            <div className="dashboard-grid">
                <div className="main-panel">
                    <div className="panel-header">
                        <h2>Analysis & Insights</h2>
                        <span className="ai-badge">AI Generated</span>
                    </div>
                    <div className="panel-content summary-content">
                        {renderContent()}
                    </div>
                </div>

                <div className="side-panel">
                    <div className="metric-card">
                        <div className="metric-header">
                            <h3>Stock Performance</h3>
                            {stockData && (
                                <span className={`change-tag ${stockData.realtime_price >= chartData[0]?.price ? 'positive' : 'negative'}`}>
                                    {stockData.currency}
                                </span>
                            )}
                        </div>
                        {stockError ? (
                            <div className="stock-error-message" style={{
                                padding: '2rem',
                                textAlign: 'center',
                                color: '#888',
                                fontSize: '0.95rem',
                                lineHeight: '1.6'
                            }}>
                                <p style={{ margin: 0 }}>{stockError}</p>
                            </div>
                        ) : (
                            <>
                                <div className="current-price">
                                    {isLoadingStock ? 'Loading...' : stockData ? `$${stockData.realtime_price?.toFixed(2)}` : 'Loading...'}
                                </div>
                                <div className="chart-container">
                                    <ResponsiveContainer width="100%" height={200}>
                                        <AreaChart data={chartData}>
                                            <defs>
                                                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                                    <stop offset="5%" stopColor="#4285f4" stopOpacity={0.3} />
                                                    <stop offset="95%" stopColor="#4285f4" stopOpacity={0} />
                                                </linearGradient>
                                            </defs>
                                            <Tooltip
                                                contentStyle={{ backgroundColor: '#1e2029', border: 'none', borderRadius: '8px' }}
                                                itemStyle={{ color: '#fff' }}
                                                labelStyle={{ color: '#888' }}
                                            />
                                            <Area
                                                type="monotone"
                                                dataKey="price"
                                                stroke="#4285f4"
                                                fillOpacity={1}
                                                fill="url(#colorPrice)"
                                                strokeWidth={2}
                                            />
                                            <XAxis dataKey="date" hide />
                                            <YAxis domain={['auto', 'auto']} hide />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </div>
                                <div className="time-filters">
                                    {['5d', '1mo', '6mo', '1y', '5y'].map(range => (
                                        <button
                                            key={range}
                                            className={`time-btn ${timeRange === range ? 'active' : ''}`}
                                            onClick={() => handleTimeRangeChange(range)}
                                        >
                                            {range.toUpperCase()}
                                        </button>
                                    ))}
                                </div>
                            </>
                        )}
                    </div>

                    <div className="metric-card">
                        <h3>Key Metrics</h3>
                        <div className="key-metrics-grid">
                            <div className="km-item">
                                <span className="km-label">Market Cap</span>
                                <span className="km-value">{metrics?.market_cap || '–'}</span>
                            </div>
                            <div className="km-item">
                                <span className="km-label">P/E Ratio</span>
                                <span className="km-value">{metrics?.pe_ratio?.toFixed(2) || '–'}</span>
                            </div>
                            <div className="km-item">
                                <span className="km-label">EPS</span>
                                <span className="km-value">{metrics?.eps?.toFixed(2) || '–'}</span>
                            </div>
                            <div className="km-item">
                                <span className="km-label">Div Yield</span>
                                <span className="km-value text-green">{metrics?.dividend_yield || '–'}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;

