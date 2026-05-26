import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, AreaChart, Area, Tooltip, XAxis, YAxis } from 'recharts';
import { Download, Share2, Info, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './Dashboard.css';

const API_URL = 'http://localhost:9001';

const Dashboard = ({ company, currentPage, activeHighlightTab, setActiveHighlightTab }) => {
    const pageSubtitles = {
        'Highlights and Takeaways': 'Latest Highlights',
        'Earnings': 'Latest Earnings Report',
        'Briefing Docs': 'Latest Briefing Doc',
        'Full Summary': 'Latest Full Summary'
    };
    const pageSubtitle = pageSubtitles[currentPage] || `Latest ${currentPage}`;

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
    const [briefingData, setBriefingData] = useState(null);
    const [isLoadingBriefing, setIsLoadingBriefing] = useState(false);
    const [showSources, setShowSources] = useState(false);
    const [modalSources, setModalSources] = useState([]);
    const [expandedSections, setExpandedSections] = useState({
        leadership: true,
        vendor_topics: true,
        pricing_insights: true,
        products_features: true,
        ai_cloud_productivity: true
    });

    const toggleSection = (secId) => {
        setExpandedSections(prev => ({
            ...prev,
            [secId]: !prev[secId]
        }));
    };
    const highlightTabs = [
        { id: 'leadership', label: 'Leadership' },
        { id: 'vendor_topics', label: 'Vendor Discussion Topics' },
        { id: 'pricing_insights', label: 'Pricing Insights' },
        { id: 'products_features', label: 'Products and Features' },
        { id: 'ai_cloud_productivity', label: 'AI, Cloud and Productivity' }
    ];

    // Clear data when company changes
    useEffect(() => {
        if (company) {
            setHighlightsData({});
            setHighlightsSources({});
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

    const refreshLiveEarnings = async () => {
        if (!company) return;

        setIsLoadingEarnings(true);
        try {
            const res = await fetch(`${API_URL}/earnings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    company_name: company.name,
                    force_live: true
                })
            });
            if (res.ok) {
                const data = await res.json();
                setEarningsData(data.earnings);
            } else {
                console.error("Failed to refresh live earnings");
            }
        } catch (err) {
            console.error("Live earnings refresh error:", err);
        } finally {
            setIsLoadingEarnings(false);
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

    // Fetch all highlights when Highlights page is open
    useEffect(() => {
        if (currentPage === 'Highlights and Takeaways' && company) {
            const tabs = ['leadership', 'vendor_topics', 'pricing_insights', 'products_features', 'ai_cloud_productivity'];
            tabs.forEach(tab => {
                if (!highlightsData[tab]) {
                    fetchHighlights(tab);
                }
            });
        }
    }, [company, currentPage, highlightsData]);


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
            title = `${company.name} - Highlights and Takeaways`;
            let docHtml = '';

            const sections = [
                { id: 'leadership', label: 'Leadership Team' },
                { id: 'vendor_topics', label: 'Vendor Discussion Topics' },
                { id: 'pricing_insights', label: 'Pricing Insights' },
                { id: 'products_features', label: 'Products and Features' },
                { id: 'ai_cloud_productivity', label: 'AI, Cloud and Productivity' }
            ];

            sections.forEach(sec => {
                const tabContent = highlightsData[sec.id] || 'No data available.';
                docHtml += `<h2>${sec.label}</h2>`;
                
                if (sec.id === 'leadership') {
                    try {
                        const parsed = JSON.parse(tabContent);
                        if (Array.isArray(parsed)) {
                            parsed.forEach(exec => {
                                docHtml += `<p><b>${exec.name}</b> - <span style="color: #4f46e5; font-weight: 600;">${exec.title}</span>${exec.since ? ` (Since ${exec.since})` : ''}</p>`;
                                docHtml += `<p style="margin-left: 20px; font-style: italic; color: #555; margin-bottom: 15px;">${exec.bio}</p>`;
                            });
                        } else {
                            docHtml += formatForDoc(tabContent);
                        }
                    } catch (e) {
                        docHtml += formatForDoc(tabContent);
                    }
                } else if (sec.id === 'vendor_topics') {
                    try {
                        const parsed = JSON.parse(tabContent);
                        if (parsed) {
                            if (parsed.pricing_strategy) {
                                docHtml += `<h4>Pricing & Packaging Strategy</h4>`;
                                docHtml += `<p>${parsed.pricing_strategy.summary}</p>`;
                                docHtml += `<p style="background-color: #fffbeb; padding: 10px; border-left: 4px solid #d97706; margin-bottom: 15px;"><b>Meeting Ask:</b> ${parsed.pricing_strategy.discussion_point}</p>`;
                            }
                            if (parsed.ai_cloud_integration) {
                                docHtml += `<h4>AI & Cloud Platform Strategy</h4>`;
                                docHtml += `<p>${parsed.ai_cloud_integration.summary}</p>`;
                                docHtml += `<p style="background-color: #faf5ff; padding: 10px; border-left: 4px solid #7c3aed; margin-bottom: 15px;"><b>Meeting Ask:</b> ${parsed.ai_cloud_integration.discussion_point}</p>`;
                            }
                            if (parsed.product_roadmap) {
                                docHtml += `<h4>Product Capability Roadmap</h4>`;
                                docHtml += `<p>${parsed.product_roadmap.summary}</p>`;
                                docHtml += `<p style="background-color: #f0f9ff; padding: 10px; border-left: 4px solid #1d4ed8; margin-bottom: 15px;"><b>Meeting Ask:</b> ${parsed.product_roadmap.discussion_point}</p>`;
                            }
                            if (parsed.security_compliance) {
                                docHtml += `<h4>Security & Risk Compliance</h4>`;
                                docHtml += `<p>${parsed.security_compliance.context || parsed.security_compliance.summary || ''}</p>`;
                                docHtml += `<p style="background-color: #fef2f2; padding: 10px; border-left: 4px solid #ef4444; margin-bottom: 15px;"><b>Meeting Ask:</b> ${parsed.security_compliance.discussion_point}</p>`;
                            }
                            if (parsed.partnership_opportunities) {
                                docHtml += `<h4>Strategic Partnership & Growth</h4>`;
                                docHtml += `<p>${parsed.partnership_opportunities.context || parsed.partnership_opportunities.summary || ''}</p>`;
                                docHtml += `<p style="background-color: #ecfdf5; padding: 10px; border-left: 4px solid #10b981; margin-bottom: 15px;"><b>Meeting Ask:</b> ${parsed.partnership_opportunities.discussion_point}</p>`;
                            }
                        } else {
                            docHtml += formatForDoc(tabContent);
                        }
                    } catch (e) {
                        docHtml += formatForDoc(tabContent);
                    }
                } else {
                    docHtml += formatForDoc(tabContent);
                }
                
                docHtml += `<hr style="border: 0; border-top: 1px solid #eee; margin: 25px 0;" />`;
            });

            content = docHtml;
        } else if (currentPage === 'Briefing Docs') {
            title = `${company.name} - Vendor Briefing Document`;
            let parsed = null;
            if (briefingData && briefingData.content) {
                try {
                    parsed = typeof briefingData.content === 'object' ? briefingData.content : JSON.parse(briefingData.content);
                } catch (e) {
                    console.error("Error parsing briefing content for export:", e);
                }
            }

            if (parsed) {
                let docHtml = `<h2>Executive Summary & Overview</h2>`;
                if (parsed.financial_health) {
                    docHtml += `<div style="background-color: #f0f4f9; border-left: 4px solid #1a73e8; padding: 12px; margin-bottom: 20px;">`;
                    docHtml += `<h3 style="margin-top: 0; color: #1a73e8;">Financial & Business Health</h3>`;
                    docHtml += `<p>${parsed.financial_health}</p>`;
                    docHtml += `</div>`;
                }

                if (parsed.account_summary) {
                    docHtml += `<h3>Company Overview</h3>`;
                    docHtml += `<p>${parsed.account_summary.company_overview || ''}</p>`;
                    
                    if (parsed.account_summary.key_highlights && parsed.account_summary.key_highlights.length > 0) {
                        docHtml += `<h4>Key Highlights</h4><ul>`;
                        parsed.account_summary.key_highlights.forEach(h => {
                            docHtml += `<li>${h}</li>`;
                        });
                        docHtml += `</ul>`;
                    }
                }

                if (parsed.business_performance) {
                    docHtml += `<h2>Business Performance Analysis</h2>`;
                    if (parsed.business_performance.strengths && parsed.business_performance.strengths.length > 0) {
                        docHtml += `<h3 style="color: #2e7d32;">Strengths</h3><ul>`;
                        parsed.business_performance.strengths.forEach(s => {
                            docHtml += `<li>${s}</li>`;
                        });
                        docHtml += `</ul>`;
                    }
                    if (parsed.business_performance.challenges && parsed.business_performance.challenges.length > 0) {
                        docHtml += `<h3 style="color: #c62828;">Challenges</h3><ul>`;
                        parsed.business_performance.challenges.forEach(c => {
                            docHtml += `<li>${c}</li>`;
                        });
                        docHtml += `</ul>`;
                    }
                }

                if (parsed.opportunities_risks) {
                    docHtml += `<h2>Strategic Outlook</h2>`;
                    if (parsed.opportunities_risks.opportunities && parsed.opportunities_risks.opportunities.length > 0) {
                        docHtml += `<h3 style="color: #00838f;">Strategic Opportunities</h3><ul>`;
                        parsed.opportunities_risks.opportunities.forEach(o => {
                            docHtml += `<li>${o}</li>`;
                        });
                        docHtml += `</ul>`;
                    }
                    if (parsed.opportunities_risks.risks && parsed.opportunities_risks.risks.length > 0) {
                        docHtml += `<h3 style="color: #ef6c00;">Key Risks & Concerns</h3><ul>`;
                        parsed.opportunities_risks.risks.forEach(r => {
                            docHtml += `<li>${r}</li>`;
                        });
                        docHtml += `</ul>`;
                    }
                }

                if (parsed.recommended_actions && parsed.recommended_actions.length > 0) {
                    docHtml += `<h2>Recommended Actions & Next Steps</h2><ol>`;
                    parsed.recommended_actions.forEach(a => {
                        docHtml += `<li style="margin-bottom: 8px;"><b>[ACTION]</b> ${a}</li>`;
                    });
                    docHtml += `</ol>`;
                }

                content = `<h1>${title}</h1>${docHtml}`;
            } else {
                content = `<h1>${title}</h1>${formatForDoc(briefingData?.content || 'No Briefing data available.')}`;
            }
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
            return (
                <div className="highlights-container stacked-container">
                    <div className="highlight-content stacked-content">
                        {/* Section 1: Leadership */}
                        <div className="highlights-section-card animate-slide-up">
                            <div className="highlights-header accordion-header" onClick={() => toggleSection('leadership')}>
                                <div className="accordion-title-group">
                                    {expandedSections['leadership'] ? <ChevronUp size={18} className="accordion-chevron" /> : <ChevronDown size={18} className="accordion-chevron" />}
                                    <h3>Leadership Team</h3>
                                </div>
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                    <span className="ai-badge">AI Generated</span>
                                    {highlightsSources['leadership'] && highlightsSources['leadership'].length > 0 && (
                                        <button
                                            className="info-btn"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setModalSources(highlightsSources['leadership']);
                                                setShowSources(true);
                                            }}
                                            title="View Sources"
                                        >
                                            <Info size={16} />
                                        </button>
                                    )}
                                </div>
                            </div>
                            {expandedSections['leadership'] && (
                                <div className="highlights-text accordion-content animate-slide-down">
                                    {!highlightsData['leadership'] ? (
                                        <div className="loading-state-mini">
                                            <div className="spinner-mini"></div>
                                            <p>Loading Leadership Profiles...</p>
                                        </div>
                                    ) : (
                                        (() => {
                                            try {
                                                const parsed = JSON.parse(highlightsData['leadership']);
                                                if (Array.isArray(parsed)) {
                                                    return (
                                                        <div className="leadership-grid">
                                                            {parsed.map((exec, idx) => (
                                                                <div key={idx} className="leadership-card">
                                                                    <div className="leadership-card-top">
                                                                        <h4 className="exec-name">{exec.name}</h4>
                                                                        <span className="exec-title">{exec.title}</span>
                                                                        {exec.since && (
                                                                            <span className="exec-since">Since {exec.since}</span>
                                                                        )}
                                                                    </div>
                                                                    <div className="leadership-card-divider"></div>
                                                                    <p className="exec-bio">{exec.bio}</p>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    );
                                                }
                                            } catch (e) {
                                                console.error("Error parsing leadership JSON:", e);
                                            }
                                            return <ReactMarkdown>{highlightsData['leadership']}</ReactMarkdown>;
                                        })()
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Section 2: Vendor Discussion Topics */}
                        <div className="highlights-section-card animate-slide-up" style={{ animationDelay: '0.1s' }}>
                            <div className="highlights-header accordion-header" onClick={() => toggleSection('vendor_topics')}>
                                <div className="accordion-title-group">
                                    {expandedSections['vendor_topics'] ? <ChevronUp size={18} className="accordion-chevron" /> : <ChevronDown size={18} className="accordion-chevron" />}
                                    <h3>Vendor Discussion Topics</h3>
                                </div>
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                    <span className="ai-badge">AI Generated</span>
                                    {highlightsSources['vendor_topics'] && highlightsSources['vendor_topics'].length > 0 && (
                                        <button
                                            className="info-btn"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setModalSources(highlightsSources['vendor_topics']);
                                                setShowSources(true);
                                            }}
                                            title="View Sources"
                                        >
                                            <Info size={16} />
                                        </button>
                                    )}
                                </div>
                            </div>
                            {expandedSections['vendor_topics'] && (
                                <div className="highlights-text accordion-content animate-slide-down">
                                    {!highlightsData['vendor_topics'] ? (
                                        <div className="loading-state-mini">
                                            <div className="spinner-mini"></div>
                                            <p>Loading Vendor Topics...</p>
                                        </div>
                                    ) : (
                                        (() => {
                                            try {
                                                const parsed = JSON.parse(highlightsData['vendor_topics']);
                                                if (parsed && (parsed.pricing_strategy || parsed.ai_cloud_integration)) {
                                                    return (
                                                        <div className="vendor-topics-grid">
                                                            {/* Topic 1: Pricing Strategy */}
                                                            {parsed.pricing_strategy && (
                                                                <div className="topic-card border-amber">
                                                                    <div className="topic-card-header bg-amber-soft">
                                                                        <div className="topic-icon-badge amber-badge">$</div>
                                                                        <div className="topic-title-wrapper">
                                                                            <h4>Pricing & Packaging Strategy</h4>
                                                                            <span className="topic-type-badge text-amber">Pricing</span>
                                                                        </div>
                                                                    </div>
                                                                    <div className="topic-card-body">
                                                                        <p className="topic-summary">{parsed.pricing_strategy.summary}</p>
                                                                        <div className="discussion-point-bubble bg-amber-bubble">
                                                                            <strong>Meeting Ask:</strong>
                                                                            <p>{parsed.pricing_strategy.discussion_point}</p>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            )}
                                                            {/* Topic 2: AI & Cloud Integration */}
                                                            {parsed.ai_cloud_integration && (
                                                                <div className="topic-card border-purple">
                                                                    <div className="topic-card-header bg-purple-soft">
                                                                        <div className="topic-icon-badge purple-badge">⚡</div>
                                                                        <div className="topic-title-wrapper">
                                                                            <h4>AI & Cloud Platform Strategy</h4>
                                                                            <span className="topic-type-badge text-purple">AI / Cloud</span>
                                                                        </div>
                                                                    </div>
                                                                    <div className="topic-card-body">
                                                                        <p className="topic-summary">{parsed.ai_cloud_integration.summary}</p>
                                                                        <div className="discussion-point-bubble bg-purple-bubble">
                                                                            <strong>Meeting Ask:</strong>
                                                                            <p>{parsed.ai_cloud_integration.discussion_point}</p>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            )}
                                                            {/* Topic 3: Product Roadmap */}
                                                            {parsed.product_roadmap && (
                                                                <div className="topic-card border-blue">
                                                                    <div className="topic-card-header bg-blue-soft">
                                                                        <div className="topic-icon-badge blue-badge">📋</div>
                                                                        <div className="topic-title-wrapper">
                                                                            <h4>Product Capability Roadmap</h4>
                                                                            <span className="topic-type-badge text-blue">Roadmap</span>
                                                                        </div>
                                                                    </div>
                                                                    <div className="topic-card-body">
                                                                        <p className="topic-summary">{parsed.product_roadmap.summary}</p>
                                                                        <div className="discussion-point-bubble bg-blue-bubble">
                                                                            <strong>Meeting Ask:</strong>
                                                                            <p>{parsed.product_roadmap.discussion_point}</p>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            )}
                                                            {/* Topic 4: Security & Compliance */}
                                                            {parsed.security_compliance && (
                                                                <div className="topic-card border-coral">
                                                                    <div className="topic-card-header bg-coral-soft">
                                                                        <div className="topic-icon-badge coral-badge">🛡️</div>
                                                                        <div className="topic-title-wrapper">
                                                                            <h4>Security & Risk Compliance</h4>
                                                                            <span className="topic-type-badge text-coral">Security</span>
                                                                        </div>
                                                                    </div>
                                                                    <div className="topic-card-body">
                                                                        <p className="topic-summary">{parsed.security_compliance.context}</p>
                                                                        <div className="discussion-point-bubble bg-coral-bubble">
                                                                            <strong>Meeting Ask:</strong>
                                                                            <p>{parsed.security_compliance.discussion_point}</p>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            )}
                                                            {/* Topic 5: Partnership Opportunities */}
                                                            {parsed.partnership_opportunities && (
                                                                <div className="topic-card border-emerald">
                                                                    <div className="topic-card-header bg-emerald-soft">
                                                                        <div className="topic-icon-badge emerald-badge">🤝</div>
                                                                        <div className="topic-title-wrapper">
                                                                            <h4>Strategic Partnership & Growth</h4>
                                                                            <span className="topic-type-badge text-emerald">Alliance</span>
                                                                        </div>
                                                                    </div>
                                                                    <div className="topic-card-body">
                                                                        <p className="topic-summary">{parsed.partnership_opportunities.context}</p>
                                                                        <div className="discussion-point-bubble bg-emerald-bubble">
                                                                            <strong>Meeting Ask:</strong>
                                                                            <p>{parsed.partnership_opportunities.discussion_point}</p>
                                                                        </div>
                                                                    </div>
                                                                </div>
                                                            )}
                                                        </div>
                                                    );
                                                }
                                            } catch (e) {
                                                console.error("Error parsing vendor topics JSON:", e);
                                            }
                                            return <ReactMarkdown>{highlightsData['vendor_topics']}</ReactMarkdown>;
                                        })()
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Section 3: Pricing Insights */}
                        <div className="highlights-section-card animate-slide-up" style={{ animationDelay: '0.2s' }}>
                            <div className="highlights-header accordion-header" onClick={() => toggleSection('pricing_insights')}>
                                <div className="accordion-title-group">
                                    {expandedSections['pricing_insights'] ? <ChevronUp size={18} className="accordion-chevron" /> : <ChevronDown size={18} className="accordion-chevron" />}
                                    <h3>Pricing Insights</h3>
                                </div>
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                    <span className="ai-badge">AI Generated</span>
                                    {highlightsSources['pricing_insights'] && highlightsSources['pricing_insights'].length > 0 && (
                                        <button
                                            className="info-btn"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setModalSources(highlightsSources['pricing_insights']);
                                                setShowSources(true);
                                            }}
                                            title="View Sources"
                                        >
                                            <Info size={16} />
                                        </button>
                                    )}
                                </div>
                            </div>
                            {expandedSections['pricing_insights'] && (
                                <div className="highlights-text accordion-content animate-slide-down">
                                    {!highlightsData['pricing_insights'] ? (
                                        <div className="loading-state-mini">
                                            <div className="spinner-mini"></div>
                                            <p>Loading Pricing Insights...</p>
                                        </div>
                                    ) : (
                                        <ReactMarkdown>{highlightsData['pricing_insights']}</ReactMarkdown>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Section 4: Products and Features */}
                        <div className="highlights-section-card animate-slide-up" style={{ animationDelay: '0.3s' }}>
                            <div className="highlights-header accordion-header" onClick={() => toggleSection('products_features')}>
                                <div className="accordion-title-group">
                                    {expandedSections['products_features'] ? <ChevronUp size={18} className="accordion-chevron" /> : <ChevronDown size={18} className="accordion-chevron" />}
                                    <h3>Products and Features</h3>
                                </div>
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                    <span className="ai-badge">AI Generated</span>
                                    {highlightsSources['products_features'] && highlightsSources['products_features'].length > 0 && (
                                        <button
                                            className="info-btn"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setModalSources(highlightsSources['products_features']);
                                                setShowSources(true);
                                            }}
                                            title="View Sources"
                                        >
                                            <Info size={16} />
                                        </button>
                                    )}
                                </div>
                            </div>
                            {expandedSections['products_features'] && (
                                <div className="highlights-text accordion-content animate-slide-down">
                                    {!highlightsData['products_features'] ? (
                                        <div className="loading-state-mini">
                                            <div className="spinner-mini"></div>
                                            <p>Loading Products and Features...</p>
                                        </div>
                                    ) : (
                                        <ReactMarkdown>{highlightsData['products_features']}</ReactMarkdown>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Section 5: AI, Cloud and Productivity */}
                        <div className="highlights-section-card animate-slide-up" style={{ animationDelay: '0.4s' }}>
                            <div className="highlights-header accordion-header" onClick={() => toggleSection('ai_cloud_productivity')}>
                                <div className="accordion-title-group">
                                    {expandedSections['ai_cloud_productivity'] ? <ChevronUp size={18} className="accordion-chevron" /> : <ChevronDown size={18} className="accordion-chevron" />}
                                    <h3>AI, Cloud and Productivity</h3>
                                </div>
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                    <span className="ai-badge">AI Generated</span>
                                    {highlightsSources['ai_cloud_productivity'] && highlightsSources['ai_cloud_productivity'].length > 0 && (
                                        <button
                                            className="info-btn"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setModalSources(highlightsSources['ai_cloud_productivity']);
                                                setShowSources(true);
                                            }}
                                            title="View Sources"
                                        >
                                            <Info size={16} />
                                        </button>
                                    )}
                                </div>
                            </div>
                            {expandedSections['ai_cloud_productivity'] && (
                                <div className="highlights-text accordion-content animate-slide-down">
                                    {!highlightsData['ai_cloud_productivity'] ? (
                                        <div className="loading-state-mini">
                                            <div className="spinner-mini"></div>
                                            <p>Loading AI, Cloud and Productivity updates...</p>
                                        </div>
                                    ) : (
                                        <ReactMarkdown>{highlightsData['ai_cloud_productivity']}</ReactMarkdown>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Sources Modal */}
                    {showSources && modalSources.length > 0 && (
                        <div className="sources-modal-overlay" onClick={() => setShowSources(false)}>
                            <div className="sources-modal" onClick={(e) => e.stopPropagation()}>
                                <div className="sources-modal-header">
                                    <h3>Sources</h3>
                                    <button className="close-btn" onClick={() => setShowSources(false)}>×</button>
                                </div>
                                <div className="sources-modal-content">
                                    {modalSources.map((source, idx) => (
                                        <div key={idx} className="source-item">
                                            <div className="source-number">{idx + 1}</div>
                                            <div className="source-details">
                                                <a href={source.url} target="_blank" rel="noopener noreferrer" className="source-title">
                                                    {source.title}
                                                </a>
                                                <div className="source-meta">
                                                    {source.date && <span className="source-date">{source.date}</span>}
                                                    <span className="source-url">
                                                        {(() => {
                                                            try {
                                                                return new URL(source.url).hostname;
                                                            } catch (e) {
                                                                return source.url;
                                                            }
                                                        })()}
                                                    </span>
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
                let parsed = null;
                try {
                    parsed = typeof briefingData.content === 'object' ? briefingData.content : JSON.parse(briefingData.content);
                } catch (e) {
                    console.error("Error parsing briefing content:", e);
                }

                if (parsed) {
                    return (
                        <div className="briefing-dashboard">
                            {/* Financial Health Callout Banner */}
                            {parsed.financial_health && (
                                <div className="briefing-health-banner animate-slide-up">
                                    <div className="banner-icon-container">
                                        <span className="banner-glow-dot"></span>
                                        <svg className="banner-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <line x1="18" y1="20" x2="18" y2="10"></line>
                                            <line x1="12" y1="20" x2="12" y2="4"></line>
                                            <line x1="6" y1="20" x2="6" y2="14"></line>
                                        </svg>
                                    </div>
                                    <div className="banner-body">
                                        <h4>Financial & Business Health</h4>
                                        <p>{parsed.financial_health}</p>
                                    </div>
                                </div>
                            )}

                            <div className="briefing-grid">
                                {/* Account Summary Card */}
                                <div className="briefing-card summary-card animate-slide-up">
                                    <div className="card-header border-blue">
                                        <h3>Account Summary</h3>
                                        <span className="section-badge badge-blue">Overview</span>
                                    </div>
                                    <div className="card-body">
                                        <p className="company-overview-text">{parsed.account_summary?.company_overview}</p>
                                        <div className="highlight-section-title">Key Highlights</div>
                                        <ul className="briefing-list">
                                            {parsed.account_summary?.key_highlights?.map((highlight, idx) => (
                                                <li key={idx} className="list-item-hover">
                                                    <span className="list-bullet bullet-blue"></span>
                                                    <p>{highlight}</p>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>

                                {/* Business Performance Card */}
                                <div className="briefing-card performance-card animate-slide-up">
                                    <div className="card-header border-purple">
                                        <h3>Business Performance</h3>
                                        <span className="section-badge badge-purple">Performance</span>
                                    </div>
                                    <div className="card-body split-grid">
                                        <div className="split-column">
                                            <div className="column-title text-green">
                                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="column-icon">
                                                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                                                    <polyline points="22 4 12 14.01 9 11.01"></polyline>
                                                </svg>
                                                Strengths
                                            </div>
                                            <ul className="briefing-list compact">
                                                {parsed.business_performance?.strengths?.map((item, idx) => (
                                                    <li key={idx} className="list-item-hover">
                                                        <span className="list-bullet bullet-green"></span>
                                                        <p>{item}</p>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                        <div className="split-column">
                                            <div className="column-title text-red">
                                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="column-icon">
                                                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                                                    <line x1="12" y1="9" x2="12" y2="13"></line>
                                                    <line x1="12" y1="17" x2="12.01" y2="17"></line>
                                                </svg>
                                                Challenges
                                            </div>
                                            <ul className="briefing-list compact">
                                                {parsed.business_performance?.challenges?.map((item, idx) => (
                                                    <li key={idx} className="list-item-hover">
                                                        <span className="list-bullet bullet-red"></span>
                                                        <p>{item}</p>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>
                                </div>

                                {/* Opportunities & Risks Card */}
                                <div className="briefing-card opportunities-card animate-slide-up">
                                    <div className="card-header border-amber">
                                        <h3>Opportunities & Risks</h3>
                                        <span className="section-badge badge-amber">Strategic Outlook</span>
                                    </div>
                                    <div className="card-body split-grid">
                                        <div className="split-column">
                                            <div className="column-title text-cyan">
                                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="column-icon">
                                                    <polygon points="12 2 2 22 22 22"></polygon>
                                                </svg>
                                                Strategic Opportunities
                                            </div>
                                            <ul className="briefing-list compact">
                                                {parsed.opportunities_risks?.opportunities?.map((item, idx) => (
                                                    <li key={idx} className="list-item-hover">
                                                        <span className="list-bullet bullet-cyan"></span>
                                                        <p>{item}</p>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                        <div className="split-column">
                                            <div className="column-title text-orange">
                                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="column-icon">
                                                    <circle cx="12" cy="12" r="10"></circle>
                                                    <line x1="12" y1="8" x2="12" y2="12"></line>
                                                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                                                </svg>
                                                Key Risks
                                            </div>
                                            <ul className="briefing-list compact">
                                                {parsed.opportunities_risks?.risks?.map((item, idx) => (
                                                    <li key={idx} className="list-item-hover">
                                                        <span className="list-bullet bullet-orange"></span>
                                                        <p>{item}</p>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>
                                </div>

                                {/* Recommended Actions Card */}
                                <div className="briefing-card actions-card animate-slide-up">
                                    <div className="card-header border-teal">
                                        <h3>Recommended Actions</h3>
                                        <span className="section-badge badge-teal">Execution</span>
                                    </div>
                                    <div className="card-body">
                                        <div className="action-intro-text">Prioritized strategic demands and next-step actions:</div>
                                        <div className="action-checklist">
                                            {parsed.recommended_actions?.map((action, idx) => (
                                                <div key={idx} className="action-item list-item-hover">
                                                    <div className="checkbox-wrapper">
                                                        <div className="custom-checkbox">
                                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="check-svg">
                                                                <polyline points="20 6 9 17 4 12"></polyline>
                                                            </svg>
                                                        </div>
                                                    </div>
                                                    <div className="action-content">
                                                        <span className="action-priority-tag">Action {idx + 1}</span>
                                                        <p>{action}</p>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                }
            }

            // Fallback rendering of markdown
            if (briefingData && briefingData.content) {
                return (
                    <div className="highlights-data-card animate-slide-up">
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
                let parsed = earningsData;
                try {
                    if (typeof earningsData === 'string') {
                        parsed = JSON.parse(earningsData);
                    }
                } catch (e) {
                    console.error("Error parsing earnings JSON:", e);
                }

                // Support both legacy "summary" and new "content" structures
                const contentText = parsed?.content || parsed?.summary || "No earnings data available.";
                const sources = parsed?.sources || [];

                return (
                    <div className="highlights-data-card animate-slide-up">
                        <div className="highlights-header">
                            <h3>Quarterly Earnings Results</h3>
                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                <span className="ai-badge">AI Generated</span>
                                <button
                                    className="sources-bubble"
                                    onClick={refreshLiveEarnings}
                                    title="Refresh with live sources"
                                >
                                    <RefreshCw size={14} />
                                    <span>Refresh Live</span>
                                </button>
                                {sources && sources.length > 0 && (
                                    <button 
                                        className="sources-bubble"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setModalSources(sources);
                                            setShowSources(true);
                                        }}
                                        title="View Sources"
                                    >
                                        <Info size={14} />
                                        <span>{sources.length} Sources</span>
                                    </button>
                                )}
                            </div>
                        </div>
                        <div className="highlights-text">
                            <ReactMarkdown>{contentText}</ReactMarkdown>
                        </div>
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

        // Other pages (Briefing Docs, Spend)
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
                    <p className="page-subtitle">{pageSubtitle} - {company.name}</p>
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
            </div>
        </div>
    );
};

export default Dashboard;


