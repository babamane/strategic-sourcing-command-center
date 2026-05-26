import React, { useState, useEffect, useRef } from 'react';
import OnboardingWizard from './OnboardingWizard';
import {
    Search, Send, ShieldAlert, TrendingUp, FileText, Users, Activity,
    ChevronRight, CheckCircle2, AlertCircle, Database, BrainCircuit,
    Clock, RefreshCw, Plus, LayoutDashboard, History, ChevronLeft, Info,
    Play, Pause, ExternalLink, Target, Zap, Loader2, ArrowUpRight, Radio,
    Building2, UserCheck, ChevronDown, XCircle, FileSearch, ShieldCheck,
    Scale, FileSignature, Check, Award, Download, Printer, UserMinus,
    Filter, ArrowLeft, BellRing, Sparkles, Cpu, Globe, Shield, FileClock,
    Gavel, Briefcase, ListChecks, Calendar, Lock, AlertTriangle, Mail, Table, CheckSquare, PieChart,
    Mic, Newspaper, GitMerge, DollarSign
} from 'lucide-react';

// --- CONSTANTS & MOCK DATA ---

const ACTIVE_AGENTS = [
    { id: 'saas',     name: 'SaaS Health & Spend',   icon: Database,    color: 'text-blue-500',    bg: 'bg-blue-50',    pillar: '01 Overall SaaS Health',       route: 'http://localhost:5174' },
    { id: 'vendor',   name: 'Vendor Intelligence',   icon: Users,       color: 'text-amber-500',   bg: 'bg-amber-50',   pillar: '02 Supplier Sourcing',         route: 'http://localhost:5173' },
    { id: 'risk',     name: 'Risk Governance',       icon: ShieldAlert, color: 'text-emerald-500', bg: 'bg-emerald-50', pillar: '03 Risk & Compliance',         route: 'http://localhost:5000' },
    { id: 'contract', name: 'Contract Execution',    icon: FileText,    color: 'text-red-500',     bg: 'bg-red-50',     pillar: '04 Negotiation & Contracting', route: 'http://localhost:8501' },
    { id: 'intel',    name: 'Risk Intelligence',     icon: Globe,       color: 'text-indigo-500',  bg: 'bg-indigo-50',  pillar: '05 Vendor Risk Intelligence',  route: 'http://localhost:8503' },
    { id: 'onboard',  name: 'Vendor Onboarding',     icon: Building2,   color: 'text-purple-500',  bg: 'bg-purple-50',  pillar: '06 Vendor Lifecycle',          route: 'onboarding' },
];

const SENTINEL_ALERTS = [
    { id: 'a1', type: 'critical', agent: 'Spend Agent', msg: 'Capacity Gap: Gemini Pro', detail: 'Forecasted demand exceeds pool by 1000 seats in Q3.', icon: TrendingUp, color: 'text-blue-600', bg: 'bg-blue-50' },
    { id: 'a2', type: 'warning', agent: 'Contract Agent', msg: 'Figma Renewal Notice', detail: '500 seats at risk of 10% auto-increase in 45 days.', icon: FileText, color: 'text-red-600', bg: 'bg-red-50' },
    { id: 'a3', type: 'info', agent: 'Risk Agent', msg: 'Vendor Drift: Slack', detail: 'Sub-processor "CloudData" reported minor SOC2 breach.', icon: ShieldAlert, color: 'text-emerald-600', bg: 'bg-emerald-50' }
];

// --- DYNAMIC MISSION BLUEPRINTS ---
const MISSIONS = {
    onboarding: {
        title: 'Launch Lifecycle Discovery',
        track: 'New Vendor Onboarding',
        icon: Building2,
        color: 'bg-amber-500',
        needsInput: true,
        steps: [
            { title: 'SUPPLIER DISCOVERY', agent: 'Vendor Agent', icon: Search, log: 'AI scan of market benchmarks and vendor profiles.', type: 'auto' },
            { title: 'QUALIFICATION REVIEW', agent: 'Compliance Agent', icon: UserCheck, log: 'Verify SOC2, ESG, and compliance credentials.', type: 'hitl_qual' },
            { title: 'RISK AUDIT', agent: 'Risk Agent', icon: ShieldCheck, log: 'Automated 24/7 financial and cyber monitoring setup.', type: 'auto' },
            { title: 'CONTRACT REVIEW', agent: 'Contract Agent', icon: FileSignature, log: 'Draft MSA review and negotiation blueprint.', type: 'hitl_contract' }
        ],
        verdict: 'GO TO ONBOARD',
        summary: 'Aggregated Logic: Vendor SOC2 Verified. ESG Grade A. Financial startup risk is fully mitigated by the 15% negotiated savings in the current MSA draft. Total saving opportunity: $42,500/year.'
    },
    a1: { // Gemini Capacity
        title: 'Capacity Remediation',
        track: 'Spend Optimization',
        icon: TrendingUp,
        color: 'bg-blue-500',
        needsInput: false,
        defaultTarget: 'gemini enterprise',
        steps: [
            { title: 'USAGE FORECAST', agent: 'Spend Agent', icon: Activity, log: 'Analyzing 12-month trailing usage and headcount growth model.', type: 'auto' },
            { title: 'RECLAMATION AUDIT', agent: 'Identity Agent', icon: UserMinus, log: 'Identify and revoke dormant licenses > 45 days.', type: 'hitl_reclaim' },
            { title: 'PROCUREMENT EXECUTION', agent: 'Procurement Agent', icon: Zap, log: 'Auto-purchasing delta licenses at pre-negotiated tier.', type: 'auto' }
        ],
        verdict: 'EXECUTE PROCUREMENT',
        summary: 'Aggregated Logic: 400 dormant seats successfully identified and queued for revocation via Okta integration. Net requirement reduced to 600 seats. Auto-procurement authorized under existing MSA terms.'
    },
    a2: { // Figma Renewal
        title: 'Renewal Negotiation',
        track: 'Contract Defense',
        icon: FileText,
        color: 'bg-red-500',
        needsInput: false,
        defaultTarget: 'figma organization',
        steps: [
            { title: 'CONTRACT PARSING', agent: 'Contract Agent', icon: FileSearch, log: 'Extracting auto-renewal terms and historical pricing baselines.', type: 'auto' },
            { title: 'USAGE AUDIT', agent: 'Spend Agent', icon: PieChart, log: 'Cross-referencing active editors vs viewer-only profiles.', type: 'auto' },
            { title: 'NEGOTIATION DRAFT', agent: 'Negotiation Agent', icon: Mail, log: 'Generating counter-proposal drafting flat renewal based on volume.', type: 'hitl_email' }
        ],
        verdict: 'PROPOSAL DISPATCHED',
        summary: 'Aggregated Logic: AI intercepted impending 10% auto-increase. Identified 120 downgrade candidates. Outbound negotiation sequence initiated to secure flat pricing at current volume levels.'
    },
    a3: { // Slack Risk
        title: 'Risk Remediation',
        track: 'Compliance Defense',
        icon: ShieldAlert,
        color: 'bg-emerald-500',
        needsInput: false,
        defaultTarget: 'slack technologies',
        steps: [
            { title: 'THREAT INTELLIGENCE', agent: 'Threat Intel Agent', icon: Globe, log: 'Querying Trust Center and BitSight for external breach details.', type: 'auto' },
            { title: 'IMPACT ANALYSIS', agent: 'Risk Agent', icon: Database, log: 'Mapping exposed sub-processor to internal data classification tiers.', type: 'auto' },
            { title: 'MITIGATION PROTOCOL', agent: 'Legal Agent', icon: ShieldCheck, log: 'Drafting DPA Addendum and targeted security questionnaire.', type: 'hitl_dpa' }
        ],
        verdict: 'MITIGATION ENFORCED',
        summary: 'Aggregated Logic: Sub-processor breach classified as Low-Impact for internal PII. Pre-emptive DPA Addendum and secondary compliance questionnaire generated and dispatched to vendor DPO.'
    }
};

// --- UNIVERSAL SHARED COMPONENTS ---

const AppHeader = ({ title, subtitle, icon: Icon, colorClass, onBack }) => (
    <header className="h-20 bg-white border-b border-slate-200 px-8 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center space-x-6">
            <button onClick={onBack} className="p-3 hover:bg-slate-100 rounded-2xl transition-colors text-slate-400 hover:text-slate-900 flex items-center space-x-2 group">
                <ArrowLeft size={20} />
                <span className="text-xs font-black uppercase tracking-widest hidden md:block">Back to Strategic Sourcing Command Center</span>
            </button>
            <div className="h-8 w-px bg-slate-100 mx-2"></div>
            <div className="flex items-center space-x-3">
                <div className={`p-2.5 ${colorClass} text-white rounded-xl shadow-lg`}><Icon size={24} /></div>
                <div>
                    <h1 className="text-xl font-black text-slate-800 tracking-tight leading-none">{title}</h1>
                    <p className="text-[10px] font-black opacity-50 uppercase tracking-widest mt-1">{subtitle}</p>
                </div>
            </div>
        </div>
    </header>
);

const StatCard = ({ title, value, subValue, trend, colorClass = "text-slate-800", icon: Icon }) => (
    <div className="bg-white p-6 rounded-[2rem] border border-slate-100 shadow-sm hover:shadow-xl transition-all group">
        <div className="flex justify-between items-start mb-2">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest group-hover:text-blue-600 transition-colors">{title}</p>
            {Icon && <Icon size={16} className="text-slate-200" />}
        </div>
        <div className="flex items-end space-x-2">
            <h3 className={`text-2xl font-black ${colorClass}`}>{value}</h3>
            {subValue && <span className="text-slate-300 text-sm font-bold pb-1">{subValue}</span>}
            {trend && <span className="text-emerald-500 text-[10px] font-bold pb-1 flex items-center tracking-tighter"><ArrowUpRight size={12} /> {trend}</span>}
        </div>
    </div>
);

const IframeApp = ({ title, subtitle, icon: Icon, colorClass, url, onBack }) => (
    <div className="min-h-screen bg-slate-50 flex flex-col animate-in fade-in duration-500 w-full h-screen absolute top-0 left-0 z-50">
        <AppHeader title={title} subtitle={subtitle} icon={Icon} colorClass={colorClass} onBack={onBack} />
        <main className="flex-1 w-full bg-white relative">
            <iframe src={url} className="w-full h-full border-0 absolute inset-0" title={title} allowFullScreen />
        </main>
    </div>
);

// --- STATEFUL APPLICATION MODULES (WITH OPERABLE FILTERS) ---

const DemandPlanningApp = ({ onBack }) => {
    const [year, setYear] = useState('2026');
    const [vendors, setVendors] = useState(['All', 'vendor_1', 'vendor_2']);
    const [tiers, setTiers] = useState(['All', 'Contributor', 'Editor', 'Full', 'Viewer']);
    const [department, setDepartment] = useState('(All)');
    const [jobPosition, setJobPosition] = useState('(All)');

    const handleVendorToggle = (v) => {
        if (v === 'All') setVendors(vendors.includes('All') ? [] : ['All', 'vendor_1', 'vendor_2']);
        else {
            let newV = vendors.includes(v) ? vendors.filter(x => x !== v) : [...vendors, v];
            if (newV.includes('vendor_1') && newV.includes('vendor_2')) newV.push('All');
            else newV = newV.filter(x => x !== 'All');
            setVendors(newV);
        }
    };

    const handleTierToggle = (t) => {
        if (t === 'All') setTiers(tiers.includes('All') ? [] : ['All', 'Contributor', 'Editor', 'Full', 'Viewer']);
        else {
            let newT = tiers.includes(t) ? tiers.filter(t => t !== t) : [...tiers, t];
            if (['Contributor', 'Editor', 'Full', 'Viewer'].every(x => newT.includes(x))) newT.push('All');
            else newT = newT.filter(x => x !== 'All');
            setTiers(newT);
        }
    };

    // Dynamic Multiplier Engine for Demo Data
    let m = 1;
    if (year === '2025') m = 0.8;
    if (year === '2024') m = 0.6;
    if (year === '(All)') m = 2.4;
    m *= (vendors.filter(v => v !== 'All').length / 2);
    m *= (tiers.filter(t => t !== 'All').length / 4);
    if (department !== '(All)') m *= 0.6;
    if (jobPosition !== '(All)') m *= 0.6;

    const scale = Math.max(0.05, m); // Protect against 0 scale
    const f = (val) => Math.round(val * m).toLocaleString();
    const fc = (val) => `$${Math.round(val * m).toLocaleString()}`;

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col animate-in fade-in duration-500">
            <AppHeader title="Demand Planning Engine" subtitle="Spend Intelligence • Pillar 01" icon={TrendingUp} colorClass="bg-blue-600" onBack={onBack} />
            <main className="flex-1 p-8 overflow-y-auto">
                <div className="max-w-[1300px] mx-auto bg-white border border-slate-200 shadow-sm p-8 text-slate-800 font-sans">
                    <h2 className="text-2xl font-bold mb-6">Demand Planning Engine</h2>

                    <div className="flex flex-col lg:flex-row gap-6">
                        {/* Left Area (Charts & Stats) */}
                        <div className="flex-1 flex flex-col gap-6">

                            {/* Top Stats Grid */}
                            <div className="grid grid-cols-4 gap-4">
                                <div className="border border-slate-200 p-5 flex flex-col items-center justify-center text-center bg-white">
                                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Total Active Seat Count</span>
                                    <span className="text-3xl font-normal text-[#3b82f6]">{f(13344)}</span>
                                </div>
                                <div className="border border-slate-200 p-5 flex flex-col items-center justify-center text-center bg-white">
                                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2 flex items-center gap-1">New Demand <span className="text-[9px] text-slate-400">({year === '(All)' ? 'ALL' : year})</span></span>
                                    <span className="text-3xl font-normal text-[#3b82f6] tracking-tight">{f(7467)} - {fc(199320)}</span>
                                </div>
                                <div className="border border-slate-200 p-5 flex flex-col items-center justify-center text-center bg-white">
                                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2 flex items-center gap-1">Renewal Pipeline <span className="text-[9px] text-slate-400">({year === '(All)' ? 'ALL' : year})</span></span>
                                    <span className="text-3xl font-normal text-[#22c55e] tracking-tight">{f(7617)} - {fc(198985)}</span>
                                </div>
                                <div className="border border-slate-200 p-5 flex flex-col items-center justify-center text-center bg-white">
                                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Reclaimable Savings</span>
                                    <span className="text-3xl font-normal text-[#22c55e] tracking-tight">{f(592)} - {fc(17045)}</span>
                                </div>
                            </div>

                            {/* Projected Growth Chart */}
                            <div className="border border-slate-200 bg-white">
                                <div className="p-4 border-b border-slate-200 flex justify-between items-start">
                                    <h3 className="font-bold text-xl text-slate-800">Projected Growth</h3>
                                    <div className="flex flex-col text-xs text-slate-500 gap-1 mt-1">
                                        <div className="flex items-center gap-2"><div className="w-3 h-3 bg-[#3b82f6]"></div> Actual Acquisitions</div>
                                        <div className="flex items-center gap-2"><div className="w-3 h-3 bg-[#f97316]"></div> Forecasted New Acquisitions</div>
                                    </div>
                                </div>
                                <div className="p-6 h-[280px] relative flex">
                                    <div className="flex flex-col justify-between text-xs text-slate-400 items-end pr-3 border-r border-slate-200 relative h-full">
                                        <span className="absolute -left-14 top-1/2 transform -translate-y-1/2 -rotate-90 whitespace-nowrap text-slate-500">Actual New Acquisitions</span>
                                        <span>800</span><span>600</span><span>400</span><span>200</span><span>0</span>
                                    </div>

                                    <div className="flex-1 relative overflow-hidden">
                                        <div className="absolute inset-0 flex flex-col justify-between"><div className="border-b border-slate-100 w-full h-0"></div><div className="border-b border-slate-100 w-full h-0"></div><div className="border-b border-slate-100 w-full h-0"></div><div className="border-b border-slate-100 w-full h-0"></div><div className="border-b border-slate-200 w-full h-0"></div></div>
                                        <svg viewBox="0 0 1000 250" className="absolute inset-0 w-full h-full transition-transform duration-500" style={{ transform: `scaleY(${scale})`, transformOrigin: 'bottom' }}>
                                            <polyline points="50,60 120,70 190,15 260,40 330,35 400,30 470,30 540,10 610,30 680,40 750,20 820,25 890,30" fill="none" stroke="#f97316" strokeWidth="3" strokeDasharray="6,6" />
                                            <polyline points="50,50 120,60 190,5" fill="none" stroke="#3b82f6" strokeWidth="3" />
                                        </svg>
                                        <div className="absolute bottom-0 left-0 w-full flex justify-between px-8 text-[10px] text-slate-400 border-t border-slate-200 pt-2 bg-white">
                                            <span>January</span><span>February</span><span>March</span><span>April</span><span>May</span><span>June</span><span>July</span><span>August</span><span>September</span><span>October</span><span>November</span><span>December</span>
                                        </div>
                                    </div>

                                    <div className="flex flex-col justify-between text-xs text-slate-400 items-start pl-3 border-l border-slate-200 relative h-full">
                                        <span className="absolute -right-20 top-1/2 transform -translate-y-1/2 -rotate-90 whitespace-nowrap text-slate-500">Forecasted New Acquisitions</span>
                                        <span>800</span><span>600</span><span>400</span><span>200</span><span>0</span>
                                    </div>
                                </div>
                            </div>

                            {/* Bottom Row Charts */}
                            <div className="grid grid-cols-2 gap-6">

                                {/* Renewal Pipeline Stacked Bar */}
                                <div className="border border-slate-200 bg-white flex flex-col">
                                    <div className="p-4 border-b border-slate-200 flex justify-between items-center">
                                        <h3 className="font-bold text-lg text-slate-800">Renewal Pipeline For {year === '(All)' ? 'ALL' : year}</h3>
                                        <div className="flex flex-col gap-1 text-[10px] text-slate-600 w-20">
                                            <div className="font-bold border-b border-slate-200 pb-1 mb-1">License Tier</div>
                                            <div className="flex items-center gap-1"><div className="w-3 h-3 bg-[#3b82f6]"></div> Editor</div>
                                            <div className="flex items-center gap-1"><div className="w-3 h-3 bg-[#ef4444]"></div> Full</div>
                                            <div className="flex items-center gap-1"><div className="w-3 h-3 bg-[#eab308]"></div> Contrib...</div>
                                            <div className="flex items-center gap-1"><div className="w-3 h-3 bg-[#22c55e]"></div> Viewer</div>
                                        </div>
                                    </div>
                                    <div className="flex-1 p-4 flex pt-6">
                                        <div className="flex flex-col justify-between text-xs text-slate-400 items-end pr-2 border-r border-slate-200 relative h-[180px]">
                                            <span className="absolute -left-10 top-1/2 transform -translate-y-1/2 -rotate-90 whitespace-nowrap text-slate-500">Projected Renewal Count</span>
                                            <span>1000</span><span>500</span><span>0</span>
                                        </div>
                                        <div className="flex-1 flex flex-col px-2">
                                            <div className="flex-1 flex justify-around items-end transition-transform duration-500" style={{ transform: `scaleY(${scale})`, transformOrigin: 'bottom' }}>
                                                {['May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'].map(m => (
                                                    <div key={m} className="w-8 h-full flex flex-col justify-end">
                                                        <div className="w-full bg-[#3b82f6]" style={{ height: `${25 + Math.random() * 10}%` }}></div>
                                                        <div className="w-full bg-[#ef4444]" style={{ height: `${30 + Math.random() * 10}%` }}></div>
                                                        <div className="w-full bg-[#eab308]" style={{ height: `${15 + Math.random() * 5}%` }}></div>
                                                        <div className="w-full bg-[#22c55e]" style={{ height: `${20 + Math.random() * 10}%` }}></div>
                                                    </div>
                                                ))}
                                            </div>
                                            <div className="flex justify-around items-end h-16 pt-2 border-t border-slate-200 mt-1">
                                                {['May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'].map(m => (
                                                    <div key={m} className="w-8 text-[10px] text-slate-500 -rotate-90 text-left pt-2" style={{ transformOrigin: 'center center' }}>{m}</div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Retention Analysis Donut */}
                                <div className="border border-slate-200 bg-white flex flex-col">
                                    <div className="p-4 border-b border-slate-200">
                                        <h3 className="font-bold text-lg text-slate-800">Retention Analysis</h3>
                                    </div>
                                    <div className="flex-1 p-4 flex items-center justify-center">
                                        <div className="relative w-56 h-56 rounded-full flex items-center justify-center shadow-inner" style={{ background: `conic-gradient(#ef4444 0% 35%, #3b82f6 35% 55%, #eab308 55% 80%, #22c55e 80% 100%)` }}>
                                            <div className="w-32 h-32 bg-white rounded-full flex items-center justify-center text-sm font-bold text-slate-600 shadow-md">
                                                {fc(17045)}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                            </div>
                        </div>

                        {/* Right Area - Operable Filters Panel */}
                        <div className="w-[280px] flex-shrink-0 flex flex-col gap-6">
                            <div className="border border-slate-200 bg-white p-6 shadow-sm">
                                <div className="mb-6">
                                    <h4 className="text-xs text-slate-600 mb-2 font-medium">Fiscal Year</h4>
                                    <div className="flex flex-col gap-2">
                                        {['(All)', '2024', '2025', '2026'].map(y => (
                                            <label key={y} className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                                                <input type="radio" name="fiscalYear" value={y} checked={year === y} onChange={() => setYear(y)} className="cursor-pointer text-blue-600 focus:ring-blue-500" />
                                                {y}
                                            </label>
                                        ))}
                                    </div>
                                </div>
                                <div className="mb-6">
                                    <h4 className="text-xs text-slate-600 mb-2 font-medium">SaaS Vendor</h4>
                                    <div className="flex flex-col gap-2">
                                        {['All', 'vendor_1', 'vendor_2'].map(v => (
                                            <label key={v} className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                                                <input type="checkbox" checked={vendors.includes(v)} onChange={() => handleVendorToggle(v)} className="cursor-pointer text-blue-600 focus:ring-blue-500 rounded-sm" />
                                                {v === 'All' ? '(All)' : v}
                                            </label>
                                        ))}
                                    </div>
                                </div>
                                <div className="mb-6">
                                    <h4 className="text-xs text-slate-600 mb-2 font-medium">License Tier</h4>
                                    <div className="flex flex-col gap-2">
                                        {['All', 'Contributor', 'Editor', 'Full', 'Viewer'].map(t => (
                                            <label key={t} className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                                                <input type="checkbox" checked={tiers.includes(t)} onChange={() => handleTierToggle(t)} className="cursor-pointer text-blue-600 focus:ring-blue-500 rounded-sm" />
                                                {t === 'All' ? '(All)' : t}
                                            </label>
                                        ))}
                                    </div>
                                </div>
                                <div className="mb-6">
                                    <h4 className="text-xs text-slate-600 mb-2 font-medium">Department</h4>
                                    <select value={department} onChange={(e) => setDepartment(e.target.value)} className="w-full border border-slate-300 rounded px-2 py-1.5 text-xs text-slate-700 outline-none focus:border-blue-500 cursor-pointer shadow-sm">
                                        <option>(All)</option>
                                        <option>Engineering</option>
                                        <option>Marketing</option>
                                        <option>Sales</option>
                                    </select>
                                </div>
                                <div>
                                    <h4 className="text-xs text-slate-600 mb-2 font-medium">Job Position</h4>
                                    <select value={jobPosition} onChange={(e) => setJobPosition(e.target.value)} className="w-full border border-slate-300 rounded px-2 py-1.5 text-xs text-slate-700 outline-none focus:border-blue-500 cursor-pointer shadow-sm">
                                        <option>(All)</option>
                                        <option>Developer</option>
                                        <option>Manager</option>
                                        <option>Director</option>
                                    </select>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>
            </main>
        </div>
    );
};

const VendorIntelligenceApp = ({ onBack }) => {
    const [vendors, setVendors] = useState(['Salesforce', 'Figma']);

    const VENDOR_INTEL_DATA = {
        'Salesforce': { score: '88/100', save: '$42k', earnings: 'Q1 FY26 Revenue $9.13B, up 11% YoY. Strong Data Cloud adoption.', price: 'List price increased 9% across Sales and Service Cloud editions.', news: 'Launched Einstein Copilot generally available. Expanding localized data zones.', ma: 'Acquired Spiff (Incentive Compensation Management).' },
        'Figma': { score: '92/100', save: '$12k', earnings: 'Private entity. Estimated ARR surpassed $600M in late 2025.', price: 'Enterprise tier introducing new AI compute add-on packages.', news: 'Launched Dev Mode 2.0 with deeper VS Code integration.', ma: 'Adobe merger officially abandoned. Continuing as independent platform.' },
        'Datadog': { score: '85/100', save: '$18k', earnings: 'Q4 Revenue $590M, up 26% YoY. Operating margin at 24%.', price: 'Optimized usage-based pricing for long-term log retention.', news: 'Released comprehensive LLM Observability suite for GenAI apps.', ma: 'Acquired Actionable (AI-driven incident remediation).' },
        'Slack': { score: '78/100', save: '$8k', earnings: 'Integrated into Salesforce financials. Enterprise Slack adoption up 14%.', price: 'Pro tier increased by $1.25/user. Enterprise unchanged.', news: 'Slack AI rolled out natively for enterprise grid customers.', ma: 'No recent M&A activity.' }
    };

    const handleVendorToggle = (v) => {
        if (v === 'All') setVendors(vendors.includes('All') ? [] : ['All', 'Salesforce', 'Figma', 'Datadog', 'Slack']);
        else {
            let newV = vendors.includes(v) ? vendors.filter(x => x !== v) : [...vendors, v];
            if (['Salesforce', 'Figma', 'Datadog', 'Slack'].every(x => newV.includes(x))) newV.push('All');
            else newV = newV.filter(x => x !== 'All');
            setVendors(newV);
        }
    };

    const activeVendors = vendors.filter(v => v !== 'All');
    const totalActive = activeVendors.length * 105 + 102; // Dynamic dummy math
    const totalSave = activeVendors.reduce((acc, v) => acc + parseInt(VENDOR_INTEL_DATA[v]?.save.replace(/\D/g, '') || 0), 0);
    const avgScore = activeVendors.length ? Math.round(activeVendors.reduce((acc, v) => acc + parseInt(VENDOR_INTEL_DATA[v]?.score.split('/')[0] || 0), 0) / activeVendors.length) : 0;

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col animate-in fade-in duration-500">
            <AppHeader title="Vendor Intelligence" subtitle="Supplier Sourcing • Pillar 02" icon={Users} colorClass="bg-amber-500" onBack={onBack} />
            <main className="flex-1 p-8 overflow-y-auto">
                <div className="max-w-[1300px] mx-auto bg-white border border-slate-200 shadow-sm p-8 text-slate-800 font-sans">
                    <h2 className="text-2xl font-bold mb-6">Supplier Intelligence Feed</h2>

                    <div className="flex flex-col lg:flex-row gap-6">
                        {/* Left Area - Dynamic Feed & Stats */}
                        <div className="flex-1 flex flex-col gap-6">
                            {/* Stats Grid */}
                            <div className="grid grid-cols-4 gap-4">
                                <div className="border border-slate-200 p-5 flex flex-col items-center justify-center text-center bg-white rounded-2xl">
                                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Tracked Vendors</span>
                                    <span className="text-3xl font-normal text-amber-500">{totalActive}</span>
                                </div>
                                <div className="border border-slate-200 p-5 flex flex-col items-center justify-center text-center bg-white rounded-2xl">
                                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Discovery Queue</span>
                                    <span className="text-3xl font-normal text-amber-500">{activeVendors.length * 3 + 2}</span>
                                </div>
                                <div className="border border-slate-200 p-5 flex flex-col items-center justify-center text-center bg-white rounded-2xl">
                                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Negotiated Savings</span>
                                    <span className="text-3xl font-normal text-[#22c55e]">${totalSave}k</span>
                                </div>
                                <div className="border border-slate-200 p-5 flex flex-col items-center justify-center text-center bg-white rounded-2xl">
                                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Avg Vendor Score</span>
                                    <span className="text-3xl font-normal text-[#3b82f6]">{avgScore}/100</span>
                                </div>
                            </div>

                            {/* Dynamic Intelligence Cards */}
                            <div className="space-y-6 mt-2">
                                {activeVendors.length === 0 ? (
                                    <div className="p-10 border border-dashed border-slate-300 rounded-2xl flex flex-col items-center justify-center text-slate-400">
                                        <Globe size={48} className="mb-4 opacity-20" />
                                        <p className="font-bold">Select a vendor to view market intelligence.</p>
                                    </div>
                                ) : (
                                    activeVendors.map(v => {
                                        const data = VENDOR_INTEL_DATA[v];
                                        if (!data) return null;
                                        return (
                                            <div key={v} className="border border-slate-200 bg-white rounded-2xl overflow-hidden shadow-sm animate-in slide-in-from-bottom-4">
                                                <div className="bg-slate-50 border-b border-slate-200 px-6 py-4 flex justify-between items-center">
                                                    <h3 className="font-black text-lg text-slate-800 flex items-center gap-2">
                                                        <Building2 size={20} className="text-amber-500" /> {v}
                                                    </h3>
                                                    <span className="text-[10px] font-bold bg-amber-100 text-amber-700 px-3 py-1 rounded-full uppercase tracking-wider flex items-center gap-1"><Radio size={12} className="animate-pulse" /> Active Monitoring</span>
                                                </div>
                                                <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                                                    <div className="flex gap-4 p-4 border border-slate-100 rounded-xl bg-slate-50/50">
                                                        <div className="mt-1 text-blue-500"><Mic size={20} /></div>
                                                        <div>
                                                            <h4 className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-1">Latest Earnings Call</h4>
                                                            <p className="text-sm text-slate-700 font-medium leading-relaxed">{data.earnings}</p>
                                                        </div>
                                                    </div>
                                                    <div className="flex gap-4 p-4 border border-slate-100 rounded-xl bg-slate-50/50">
                                                        <div className="mt-1 text-emerald-500"><DollarSign size={20} /></div>
                                                        <div>
                                                            <h4 className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-1">Pricing Changes</h4>
                                                            <p className="text-sm text-slate-700 font-medium leading-relaxed">{data.price}</p>
                                                        </div>
                                                    </div>
                                                    <div className="flex gap-4 p-4 border border-slate-100 rounded-xl bg-slate-50/50">
                                                        <div className="mt-1 text-purple-500"><Newspaper size={20} /></div>
                                                        <div>
                                                            <h4 className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-1">Market News</h4>
                                                            <p className="text-sm text-slate-700 font-medium leading-relaxed">{data.news}</p>
                                                        </div>
                                                    </div>
                                                    <div className="flex gap-4 p-4 border border-slate-100 rounded-xl bg-slate-50/50">
                                                        <div className="mt-1 text-amber-500"><GitMerge size={20} /></div>
                                                        <div>
                                                            <h4 className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-1">M&A / Innovation</h4>
                                                            <p className="text-sm text-slate-700 font-medium leading-relaxed">{data.ma}</p>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })
                                )}
                            </div>
                        </div>

                        {/* Right Area - Operable Filters Panel */}
                        <div className="w-[280px] flex-shrink-0 flex flex-col gap-6">
                            <div className="border border-slate-200 bg-white p-6 shadow-sm rounded-2xl">
                                <div className="mb-6">
                                    <h4 className="text-xs text-slate-600 mb-4 font-bold uppercase tracking-wider">Monitored Vendors</h4>
                                    <div className="flex flex-col gap-3">
                                        {['All', 'Salesforce', 'Figma', 'Datadog', 'Slack'].map(v => (
                                            <label key={v} className="flex items-center gap-3 text-sm text-slate-700 cursor-pointer group">
                                                <div className="relative flex items-center">
                                                    <input type="checkbox" checked={vendors.includes(v)} onChange={() => handleVendorToggle(v)} className="w-4 h-4 cursor-pointer text-amber-500 focus:ring-amber-500 border-slate-300 rounded" />
                                                </div>
                                                <span className="group-hover:text-amber-600 transition-colors font-medium">{v === 'All' ? '(Select All)' : v}</span>
                                            </label>
                                        ))}
                                    </div>
                                </div>
                                <div className="border-t border-slate-100 pt-6">
                                    <h4 className="text-xs text-slate-600 mb-4 font-bold uppercase tracking-wider">Intelligence Sources</h4>
                                    <div className="flex flex-col gap-3">
                                        <label className="flex items-center text-xs text-slate-600 font-medium">
                                            <CheckSquare size={16} className="text-emerald-500 mr-2" /> SEC Filings (10-K/Q)
                                        </label>
                                        <label className="flex items-center text-xs text-slate-600 font-medium">
                                            <CheckSquare size={16} className="text-emerald-500 mr-2" /> Trust Center Audits
                                        </label>
                                        <label className="flex items-center text-xs text-slate-600 font-medium">
                                            <CheckSquare size={16} className="text-emerald-500 mr-2" /> Market PR Newswire
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

const RiskGovernanceApp = ({ onBack }) => {
    const [vendors, setVendors] = useState(['All', 'Salesforce', 'Figma', 'Datadog', 'Slack']);

    const RISK_DATA = {
        'Salesforce': { health: 95, breaches: 0, gap: 2.1, audits: 2, findings: [{ title: 'SOC2 Type II Renewed', risk: 'Low', color: 'text-emerald-500', bg: 'bg-emerald-50', icon: ShieldCheck, detail: 'Annual audit completed with zero exceptions.' }] },
        'Figma': { health: 88, breaches: 0, gap: 4.5, audits: 1, findings: [{ title: 'Pending ESG Report', risk: 'Medium', color: 'text-amber-500', bg: 'bg-amber-50', icon: AlertCircle, detail: '2025 sustainability metrics pending publication.' }] },
        'Datadog': { health: 92, breaches: 0, gap: 1.2, audits: 3, findings: [{ title: 'Data Residency Review', risk: 'Low', color: 'text-blue-500', bg: 'bg-blue-50', icon: Globe, detail: 'EU-local storage compliance verified.' }] },
        'Slack': { health: 74, breaches: 1, gap: 12.4, audits: 4, findings: [{ title: 'Sub-processor Breach', risk: 'High', color: 'text-red-500', bg: 'bg-red-50', icon: ShieldAlert, detail: '"CloudData" vendor compromised. DPA addendum required.' }] }
    };

    const handleVendorToggle = (v) => {
        if (v === 'All') setVendors(vendors.includes('All') ? [] : ['All', 'Salesforce', 'Figma', 'Datadog', 'Slack']);
        else {
            let newV = vendors.includes(v) ? vendors.filter(x => x !== v) : [...vendors, v];
            if (['Salesforce', 'Figma', 'Datadog', 'Slack'].every(x => newV.includes(x))) newV.push('All');
            else newV = newV.filter(x => x !== 'All');
            setVendors(newV);
        }
    };

    const activeVendors = vendors.filter(v => v !== 'All');

    const avgHealth = activeVendors.length ? Math.round(activeVendors.reduce((acc, v) => acc + RISK_DATA[v].health, 0) / activeVendors.length) : 0;
    const totalBreaches = activeVendors.reduce((acc, v) => acc + RISK_DATA[v].breaches, 0);
    const avgGap = activeVendors.length ? (activeVendors.reduce((acc, v) => acc + RISK_DATA[v].gap, 0) / activeVendors.length).toFixed(1) : 0;
    const totalAudits = activeVendors.reduce((acc, v) => acc + RISK_DATA[v].audits, 0) + (activeVendors.length * 2);

    let activeFindings = [];
    activeVendors.forEach(v => {
        RISK_DATA[v].findings.forEach(f => activeFindings.push({ ...f, vendor: v }));
    });

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col animate-in fade-in duration-500">
            <AppHeader title="Risk Governance" subtitle="Compliance & Monitoring • Pillar 03" icon={ShieldAlert} colorClass="bg-emerald-600" onBack={onBack} />
            <main className="flex-1 p-8 overflow-y-auto">
                <div className="max-w-[1300px] mx-auto bg-white border border-slate-200 shadow-sm p-8 text-slate-800 font-sans">
                    <h2 className="text-2xl font-bold mb-6">Compliance & Risk Posture</h2>

                    <div className="flex flex-col lg:flex-row gap-6">
                        <div className="flex-1 flex flex-col gap-6">
                            {/* Stats Grid */}
                            <div className="grid grid-cols-4 gap-4">
                                <div className="border border-slate-200 p-5 flex flex-col items-center justify-center text-center bg-white rounded-2xl">
                                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Portfolio Health</span>
                                    <span className={`text-3xl font-normal ${avgHealth > 85 ? 'text-emerald-500' : 'text-amber-500'}`}>{avgHealth}%</span>
                                </div>
                                <div className="border border-slate-200 p-5 flex flex-col items-center justify-center text-center bg-white rounded-2xl">
                                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Critical Breaches</span>
                                    <span className={`text-3xl font-normal ${totalBreaches > 0 ? 'text-red-500' : 'text-slate-300'}`}>{totalBreaches}</span>
                                </div>
                                <div className="border border-slate-200 p-5 flex flex-col items-center justify-center text-center bg-white rounded-2xl">
                                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Compliance Gap</span>
                                    <span className="text-3xl font-normal text-amber-500">{avgGap}%</span>
                                </div>
                                <div className="border border-slate-200 p-5 flex flex-col items-center justify-center text-center bg-white rounded-2xl">
                                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Active Audits</span>
                                    <span className="text-3xl font-normal text-blue-500">{totalAudits}</span>
                                </div>
                            </div>

                            {/* Dynamic Findings List */}
                            <div className="bg-white border border-slate-200 rounded-[2.5rem] shadow-sm p-8">
                                <div className="flex justify-between items-center mb-8">
                                    <h4 className="text-lg font-black text-slate-800 tracking-tight flex items-center gap-2"><Activity size={20} className="text-emerald-500" /> Real-Time Findings</h4>
                                    <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">{activeFindings.length} Items Flagged</span>
                                </div>

                                <div className="space-y-4">
                                    {activeFindings.length === 0 ? (
                                        <div className="p-10 border border-dashed border-slate-300 rounded-2xl flex flex-col items-center justify-center text-slate-400">
                                            <Shield size={48} className="mb-4 opacity-20" />
                                            <p className="font-bold">Select a vendor to view compliance status.</p>
                                        </div>
                                ) : (
                                    activeFindings.map((item, i) => {
                                        const ItemIcon = item.icon;
                                        return (
                                            <div key={i} className="flex gap-5 p-5 bg-slate-50 rounded-2xl border border-slate-100 hover:border-slate-200 transition-colors group">
                                                <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${item.bg} ${item.color} flex-shrink-0`}>
                                                    <ItemIcon size={20} />
                                                </div>
                                                <div className="flex-1">
                                                    <div className="flex justify-between items-start mb-1">
                                                        <h5 className="font-bold text-slate-800 text-sm group-hover:text-blue-600 transition-colors">{item.title}</h5>
                                                        <span className={`text-[10px] font-black uppercase tracking-widest ${item.color} bg-white px-2 py-0.5 rounded shadow-sm border border-slate-100`}>{item.risk} Risk</span>
                                                    </div>
                                                    <p className="text-xs text-slate-500 font-medium mb-2">{item.detail}</p>
                                                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest"><Building2 size={10} className="inline mr-1" /> Vendor: {item.vendor}</p>
                                                </div>
                                            </div>
                                        );
                                    })
                                )}
                                </div>
                            </div>
                        </div>

                        {/* Right Area - Operable Filters Panel */}
                        <div className="w-[280px] flex-shrink-0 flex flex-col gap-6">
                            <div className="border border-slate-200 bg-white p-6 shadow-sm rounded-2xl">
                                <div className="mb-6">
                                    <h4 className="text-xs text-slate-600 mb-4 font-bold uppercase tracking-wider">Monitored Vendors</h4>
                                    <div className="flex flex-col gap-3">
                                        {['All', 'Salesforce', 'Figma', 'Datadog', 'Slack'].map(v => (
                                            <label key={v} className="flex items-center gap-3 text-sm text-slate-700 cursor-pointer group">
                                                <div className="relative flex items-center">
                                                    <input type="checkbox" checked={vendors.includes(v)} onChange={() => handleVendorToggle(v)} className="w-4 h-4 cursor-pointer text-emerald-500 focus:ring-emerald-500 border-slate-300 rounded" />
                                                </div>
                                                <span className="group-hover:text-emerald-600 transition-colors font-medium">{v === 'All' ? '(Select All)' : v}</span>
                                            </label>
                                        ))}
                                    </div>
                                </div>
                                <div className="border-t border-slate-100 pt-6">
                                    <h4 className="text-xs text-slate-600 mb-4 font-bold uppercase tracking-wider">Compliance Frameworks</h4>
                                    <div className="flex flex-col gap-3">
                                        <label className="flex items-center text-xs text-slate-600 font-medium">
                                            <CheckSquare size={16} className="text-blue-500 mr-2" /> SOC2 Type II
                                        </label>
                                        <label className="flex items-center text-xs text-slate-600 font-medium">
                                            <CheckSquare size={16} className="text-blue-500 mr-2" /> ISO 27001
                                        </label>
                                        <label className="flex items-center text-xs text-slate-600 font-medium">
                                            <CheckSquare size={16} className="text-blue-500 mr-2" /> GDPR / CCPA
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

const ContractExecutionApp = ({ onBack }) => {
    const [vendors, setVendors] = useState(['All', 'Salesforce', 'Figma', 'Datadog', 'Slack']);

    const CONTRACT_DATA = {
        'Salesforce': { msas: 12, roi: 85, drafts: 2, renewal: { m: 'APR', date: 'Apr 22, 2026', critical: false, terms: 'Flat renewal pre-negotiated. Volume discount applied.' } },
        'Datadog': { msas: 5, roi: 45, drafts: 0, renewal: { m: 'MAY', date: 'May 10, 2026', critical: false, terms: 'Usage-based tier optimization approved.' } },
        'Figma': { msas: 3, roi: 12, drafts: 1, renewal: { m: 'JUN', date: 'Jun 15, 2026', critical: true, terms: '10% auto-increase impending. Negotiation required.' } },
        'Slack': { msas: 8, roi: 22, drafts: 3, renewal: { m: 'AUG', date: 'Aug 01, 2026', critical: false, terms: 'Consolidating to Enterprise Grid.' } }
    };

    const handleVendorToggle = (v) => {
        if (v === 'All') setVendors(vendors.includes('All') ? [] : ['All', 'Salesforce', 'Figma', 'Datadog', 'Slack']);
        else {
            let newV = vendors.includes(v) ? vendors.filter(x => x !== v) : [...vendors, v];
            if (['Salesforce', 'Figma', 'Datadog', 'Slack'].every(x => newV.includes(x))) newV.push('All');
            else newV = newV.filter(x => x !== 'All');
            setVendors(newV);
        }
    };

    const activeVendors = vendors.filter(v => v !== 'All');

    const totalMsas = activeVendors.reduce((acc, v) => acc + CONTRACT_DATA[v].msas, 0) + (activeVendors.length * 52);
    const totalRoi = activeVendors.reduce((acc, v) => acc + CONTRACT_DATA[v].roi, 0) + (activeVendors.length * 15);
    const totalDrafts = activeVendors.reduce((acc, v) => acc + CONTRACT_DATA[v].drafts, 0);
    const criticalRenewals = activeVendors.filter(v => CONTRACT_DATA[v].renewal.critical).length;

    const timelineItems = activeVendors
        .map(v => ({ ...CONTRACT_DATA[v].renewal, vendor: v }))
        .sort((a, b) => {
            const months = { 'APR': 4, 'MAY': 5, 'JUN': 6, 'JUL': 7, 'AUG': 8 };
            return months[a.m] - months[b.m];
        });

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col animate-in fade-in duration-500">
            <AppHeader title="Contract Execution" subtitle="Negotiation & Lifecycle • Pillar 04" icon={FileText} colorClass="bg-red-500" onBack={onBack} />
            <main className="flex-1 p-8 overflow-y-auto">
                <div className="max-w-[1300px] mx-auto bg-white border border-slate-200 shadow-sm p-8 text-slate-800 font-sans">
                    <h2 className="text-2xl font-bold mb-6">Contract Lifecycle Engine</h2>

                    <div className="flex flex-col lg:flex-row gap-6">
                        <div className="flex-1 flex flex-col gap-6">
                            {/* Stats Grid */}
                            <div className="grid grid-cols-4 gap-4">
                                <div className="border border-slate-200 p-5 flex flex-col items-center justify-center text-center bg-white rounded-2xl">
                                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Active Agreements</span>
                                    <span className="text-3xl font-normal text-slate-800">{totalMsas}</span>
                                </div>
                                <div className="border border-slate-200 p-5 flex flex-col items-center justify-center text-center bg-white rounded-2xl">
                                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Renewals &lt; 90 Days</span>
                                    <span className={`text-3xl font-normal ${criticalRenewals > 0 ? 'text-red-500' : 'text-emerald-500'}`}>{criticalRenewals + (activeVendors.length > 0 ? 3 : 0)}</span>
                                </div>
                                <div className="border border-slate-200 p-5 flex flex-col items-center justify-center text-center bg-white rounded-2xl">
                                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Negotiated ROI</span>
                                    <span className="text-3xl font-normal text-emerald-500">${totalRoi}k</span>
                                </div>
                                <div className="border border-slate-200 p-5 flex flex-col items-center justify-center text-center bg-white rounded-2xl">
                                    <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-2">Drafts Pending</span>
                                    <span className="text-3xl font-normal text-blue-500">{totalDrafts}</span>
                                </div>
                            </div>

                            {/* Dynamic Renewal Timeline */}
                            <div className="bg-white p-8 rounded-[2.5rem] border border-slate-100 shadow-sm">
                                <h4 className="text-lg font-black text-slate-800 tracking-tight mb-12 flex items-center space-x-2">
                                    <Calendar size={20} className="text-red-500" />
                                    <span>Upcoming Renewal Timeline</span>
                                </h4>

                                {timelineItems.length === 0 ? (
                                    <div className="p-10 border border-dashed border-slate-300 rounded-2xl flex flex-col items-center justify-center text-slate-400">
                                        <FileClock size={48} className="mb-4 opacity-20" />
                                        <p className="font-bold">Select a vendor to view upcoming renewals.</p>
                                    </div>
                                ) : (
                                    <div className="relative pb-8">
                                        <div className="absolute top-4 left-0 right-0 h-1 bg-slate-100 rounded-full"></div>
                                        <div className="flex justify-between relative z-10">
                                            {timelineItems.map((item, i) => (
                                                <div key={i} className="flex flex-col items-center group w-1/4">
                                                    <div className={`w-8 h-8 rounded-full border-4 border-white shadow-lg mb-4 transition-transform group-hover:scale-125 ${item.critical ? 'bg-red-500 animate-pulse' : 'bg-blue-500'}`}></div>
                                                    <span className="text-[10px] font-black text-slate-400 mb-1">{item.m}</span>
                                                    <span className="text-sm font-black text-slate-800 mb-1">{item.vendor}</span>
                                                    <span className="text-[10px] font-bold text-slate-400 mb-4">{item.date}</span>

                                                    <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute top-20 bg-slate-800 text-white text-xs p-3 rounded-xl shadow-xl w-48 text-center z-20 pointer-events-none">
                                                        <p className="font-bold mb-1">{item.critical ? 'Action Required' : 'On Track'}</p>
                                                        <p className="text-slate-300 text-[10px] leading-tight">{item.terms}</p>
                                                        <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 w-4 h-4 bg-slate-800 rotate-45"></div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Right Area - Operable Filters Panel */}
                        <div className="w-[280px] flex-shrink-0 flex flex-col gap-6">
                            <div className="border border-slate-200 bg-white p-6 shadow-sm rounded-2xl">
                                <div className="mb-6">
                                    <h4 className="text-xs text-slate-600 mb-4 font-bold uppercase tracking-wider">Tracked Contracts</h4>
                                    <div className="flex flex-col gap-3">
                                        {['All', 'Salesforce', 'Figma', 'Datadog', 'Slack'].map(v => (
                                            <label key={v} className="flex items-center gap-3 text-sm text-slate-700 cursor-pointer group">
                                                <div className="relative flex items-center">
                                                    <input type="checkbox" checked={vendors.includes(v)} onChange={() => handleVendorToggle(v)} className="w-4 h-4 cursor-pointer text-red-500 focus:ring-red-500 border-slate-300 rounded" />
                                                </div>
                                                <span className="group-hover:text-red-600 transition-colors font-medium">{v === 'All' ? '(Select All)' : v}</span>
                                            </label>
                                        ))}
                                    </div>
                                </div>
                                <div className="border-t border-slate-100 pt-6">
                                    <h4 className="text-xs text-slate-600 mb-4 font-bold uppercase tracking-wider">Contract Type</h4>
                                    <div className="flex flex-col gap-3">
                                        <label className="flex items-center text-xs text-slate-600 font-medium">
                                            <CheckSquare size={16} className="text-blue-500 mr-2" /> Master Services (MSA)
                                        </label>
                                        <label className="flex items-center text-xs text-slate-600 font-medium">
                                            <CheckSquare size={16} className="text-blue-500 mr-2" /> Statement of Work (SOW)
                                        </label>
                                        <label className="flex items-center text-xs text-slate-600 font-medium">
                                            <CheckSquare size={16} className="text-slate-300 mr-2" /> Non-Disclosure (NDA)
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};


// --- CORE APPLICATION COMPONENT ---

const App = () => {
    const [view, setView] = useState('dashboard');
    const [activeMissionKey, setActiveMissionKey] = useState(null);
    const [missionStatus, setMissionStatus] = useState('idle');
    const [logs, setLogs] = useState([]);
    const pulseRef = useRef(null);

    const [onboardingVendor, setOnboardingVendor] = useState('');
    const [leftPanelVisible, setLeftPanelVisible] = useState(true);
    const [rightPanelVisible, setRightPanelVisible] = useState(true);
    const [currentStepIndex, setCurrentStepIndex] = useState(-1);
    const [completedSteps, setCompletedSteps] = useState([]);
    const [sessionId, setSessionId] = useState(null);
    const [sessionData, setSessionData] = useState(null);
    const ONBOARDING_API = 'http://localhost:8090';

    const currentBlueprint = activeMissionKey ? MISSIONS[activeMissionKey] : null;

    useEffect(() => {
        if (pulseRef.current) pulseRef.current.scrollTop = pulseRef.current.scrollHeight;
    }, [logs]);

    // Poll backend for real session data while pipeline is active
    useEffect(() => {
        if (!sessionId || !['running', 'hitl'].includes(missionStatus)) return;
        const interval = setInterval(() => {
            fetch(`${ONBOARDING_API}/sessions/${sessionId}`)
                .then(r => r.json())
                .then(data => setSessionData(data))
                .catch(() => {});
        }, 2500);
        return () => clearInterval(interval);
    }, [sessionId, missionStatus]);

    // Handle Dynamic Automated Steps Timer Logic
    useEffect(() => {
        let timer;
        if (missionStatus === 'running' && currentBlueprint && currentStepIndex >= 0 && currentStepIndex < currentBlueprint.steps.length) {

            const stepData = currentBlueprint.steps[currentStepIndex];

            timer = setTimeout(() => {
                // If this step requires HITL, pause execution
                if (stepData.type.startsWith('hitl_')) {
                    setMissionStatus('hitl');
                    setLogs(prev => [...prev, { agent: stepData.agent, msg: `HITL Pause: ${stepData.title}`, reason: stepData.log, time: 'NOW' }]);
                } else {
                    // Auto-complete step and move forward
                    setCompletedSteps(prev => [...prev, currentStepIndex]);
                    setLogs(prev => [...prev, { agent: stepData.agent, msg: `${stepData.title} Executed.`, reason: stepData.log, time: 'NOW' }]);

                    if (currentStepIndex + 1 === currentBlueprint.steps.length) {
                        setMissionStatus('decision_terminal');
                        setLogs(prev => [...prev, { agent: 'Orchestrator', msg: 'Pipeline execution complete.', reason: 'All autonomous steps finished. Awaiting final decision.', time: 'NOW' }]);
                    } else {
                        setCurrentStepIndex(prev => prev + 1);
                    }
                }
            }, 2000);
        }
        return () => clearTimeout(timer);
    }, [missionStatus, currentStepIndex, currentBlueprint]);

    const handleAlertClick = (alert) => {
        const missionKey = alert.id; // Maps a1, a2, a3 to MISSIONS
        setActiveMissionKey(missionKey);
        setLogs([{ agent: 'Orchestrator', msg: `Intercepted Sentinel Alert: ${alert.msg}`, reason: `Auto-generating remediation blueprint for ${alert.agent}.`, time: 'NOW' }]);
        setCompletedSteps([]);
        setCurrentStepIndex(-1);
        setOnboardingVendor(MISSIONS[missionKey].defaultTarget);
        setMissionStatus('planning');
        setView('active_mission');
    };

    const handleNewOnboarding = () => {
        setActiveMissionKey('onboarding');
        setLogs([]);
        setCompletedSteps([]);
        setCurrentStepIndex(-1);
        setOnboardingVendor('');
        setMissionStatus('awaiting_input');
        setView('active_mission');
    };

    const startBlueprint = () => {
        setMissionStatus('planning');
        setLogs([{ agent: 'Orchestrator', msg: `Initializing discovery for: ${onboardingVendor}`, reason: "User requested onboarding mission. Building execution blueprint.", time: "NOW" }]);
    };

    const launchMission = () => {
        setMissionStatus('running');
        setCurrentStepIndex(0);
        setSessionId(null);
        setSessionData(null);
        setLogs([{ agent: 'Orchestrator', msg: "Mission Launched.", reason: `Executing step 1: ${currentBlueprint.steps[0].title}.`, time: "LIVE" }]);

        // Onboarding goes to its own full-screen wizard
        if (activeMissionKey === 'onboarding') {
            setView('onboarding_wizard');
            return;
        }

        // Start real backend session for onboarding missions
        if (activeMissionKey === 'onboarding' && onboardingVendor) {
            fetch(`${ONBOARDING_API}/sessions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vendor_name: onboardingVendor }),
            })
                .then(r => r.json())
                .then(data => {
                    setSessionId(data.id);
                    setSessionData(data);
                    setLogs(prev => [...prev, { agent: 'Discovery Agent', msg: `Session started — ID: ${data.id}`, reason: 'Backend GenAI pipeline initialised.', time: 'LIVE' }]);
                })
                .catch(() => {
                    setLogs(prev => [...prev, { agent: 'Orchestrator', msg: 'Backend offline — running simulation mode.', reason: 'Could not reach http://localhost:8090', time: 'WARN' }]);
                });
        }
    };

    const handleHitlApproval = () => {
        // Call real backend if session exists
        if (sessionId && currentBlueprint) {
            const step  = currentBlueprint.steps[currentStepIndex];
            const stage = step?.type === 'hitl_qual' ? 'qualification' : 'contract';
            fetch(`${ONBOARDING_API}/sessions/${sessionId}/approve/${stage}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ decision: 'approve', notes: '', overrides: {} }),
            })
                .then(r => r.json())
                .then(data => {
                    setSessionData(data);
                    setLogs(prev => [...prev, { agent: 'Orchestrator', msg: `${stage} approved — backend confirmed.`, reason: 'GenAI pipeline resuming next stage.', time: 'NOW' }]);
                })
                .catch(() => {});
        }

        setCompletedSteps(prev => [...prev, currentStepIndex]);
        setLogs(prev => [...prev, { agent: 'Orchestrator', msg: 'Human Approval Received.', reason: 'HITL cleared. Resuming autonomous execution.', time: 'NOW' }]);

        if (currentStepIndex + 1 === currentBlueprint.steps.length) {
            setMissionStatus('decision_terminal');
        } else {
            setCurrentStepIndex(prev => prev + 1);
            setMissionStatus('running');
        }
    };

    const handleConfirmMission = () => {
        setMissionStatus('completed');
        setLogs(prev => [...prev, { agent: 'Orchestrator', msg: 'Mission Successfully Completed.', reason: 'Execution finalized and recorded to portfolio audit logs.', time: 'NOW' }]);
    };

    // UI Helper for dynamic HITL content
    const renderHitlContent = (type) => {
        const qual     = sessionData?.qualification;
        const contract = sessionData?.contract;
        switch (type) {
            case 'hitl_qual':
                return (
                    <div className="space-y-4 mb-6">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="bg-white border border-[#e2e8f0] rounded-2xl p-5 shadow-sm">
                                <p className="text-[10px] font-black text-[#94a3b8] uppercase tracking-[0.15em] mb-3">SOC2 Status</p>
                                <div className="flex items-center space-x-2 text-[#059669]">
                                    <CheckCircle2 size={18} strokeWidth={2.5} />
                                    <span className="font-bold text-[15px]">{qual?.soc2_status || 'Verified - Type II'}</span>
                                </div>
                            </div>
                            <div className="bg-white border border-[#e2e8f0] rounded-2xl p-5 shadow-sm">
                                <p className="text-[10px] font-black text-[#94a3b8] uppercase tracking-[0.15em] mb-3">ESG Audit</p>
                                <div className="flex items-center space-x-2 text-[#059669]">
                                    <Award size={18} strokeWidth={2.5} />
                                    <span className="font-bold text-[15px]">Grade {qual?.esg_grade || 'A'}</span>
                                </div>
                            </div>
                            <div className="bg-white border border-[#e2e8f0] rounded-2xl p-5 shadow-sm">
                                <p className="text-[10px] font-black text-[#94a3b8] uppercase tracking-[0.15em] mb-3">ISO 27001</p>
                                <div className="flex items-center space-x-2 text-[#059669]">
                                    <ShieldCheck size={18} strokeWidth={2.5} />
                                    <span className="font-bold text-[15px]">{qual?.iso27001 || 'Certified'}</span>
                                </div>
                            </div>
                            <div className="bg-white border border-[#e2e8f0] rounded-2xl p-5 shadow-sm">
                                <p className="text-[10px] font-black text-[#94a3b8] uppercase tracking-[0.15em] mb-3">GDPR</p>
                                <div className="flex items-center space-x-2 text-[#059669]">
                                    <CheckCircle2 size={18} strokeWidth={2.5} />
                                    <span className="font-bold text-[15px]">{qual?.gdpr_compliant !== false ? 'Compliant' : 'Non-Compliant'}</span>
                                </div>
                            </div>
                        </div>
                        {qual?.compliance_notes && (
                            <div className="bg-[#f0fdf4] border border-[#bbf7d0] rounded-xl p-4 text-[12px] text-[#166534] font-medium">
                                {qual.compliance_notes}
                            </div>
                        )}
                    </div>
                );
            case 'hitl_contract':
                return (
                    <div className="space-y-4 mb-6">
                        {/* Contract Terms Grid */}
                        <div className="grid grid-cols-2 gap-3">
                            <div className="bg-white border border-[#e2e8f0] rounded-2xl p-4 shadow-sm">
                                <p className="text-[10px] font-black text-[#94a3b8] uppercase tracking-[0.15em] mb-2">Contract Term</p>
                                <span className="font-bold text-[14px] text-[#0f172a]">{contract?.suggested_term || '24 months'}</span>
                            </div>
                            <div className="bg-white border border-[#e2e8f0] rounded-2xl p-4 shadow-sm">
                                <p className="text-[10px] font-black text-[#94a3b8] uppercase tracking-[0.15em] mb-2">Payment Terms</p>
                                <span className="font-bold text-[14px] text-[#0f172a]">{contract?.payment_terms || 'Net 30'}</span>
                            </div>
                            <div className="bg-white border border-[#e2e8f0] rounded-2xl p-4 shadow-sm">
                                <p className="text-[10px] font-black text-[#94a3b8] uppercase tracking-[0.15em] mb-2">SLA Uptime</p>
                                <div className="flex items-center space-x-2 text-[#059669]">
                                    <CheckCircle2 size={15} strokeWidth={2.5} />
                                    <span className="font-bold text-[14px]">{contract?.sla_uptime || '99.9%'}</span>
                                </div>
                            </div>
                            <div className="bg-white border border-[#e2e8f0] rounded-2xl p-4 shadow-sm">
                                <p className="text-[10px] font-black text-[#94a3b8] uppercase tracking-[0.15em] mb-2">Termination Notice</p>
                                <span className="font-bold text-[14px] text-[#0f172a]">{contract?.termination_notice || '60 days'}</span>
                            </div>
                        </div>
                        {/* Price Protection */}
                        {contract?.price_protection && (
                            <div className="bg-[#f0fdf4] border-l-4 border-[#10b981] rounded-r-xl p-4 flex items-start space-x-3">
                                <Zap size={16} className="text-[#10b981] mt-0.5 flex-shrink-0" fill="currentColor" />
                                <div>
                                    <p className="text-[10px] font-black text-[#059669] uppercase tracking-widest mb-1">Price Protection Clause</p>
                                    <p className="text-[12px] text-[#065f46] font-medium leading-relaxed">{contract.price_protection}</p>
                                </div>
                            </div>
                        )}
                        {/* Negotiation Blueprint */}
                        {contract?.negotiation_blueprint?.length > 0 && (
                            <div className="bg-white border border-[#e2e8f0] rounded-2xl p-4 shadow-sm">
                                <p className="text-[10px] font-black text-[#94a3b8] uppercase tracking-[0.15em] mb-3">Negotiation Blueprint</p>
                                <div className="space-y-2">
                                    {contract.negotiation_blueprint.map((pt, i) => (
                                        <div key={i} className="bg-[#f8fafc] rounded-xl p-3 border border-[#e2e8f0]">
                                            <p className="text-[11px] font-black text-[#334155] uppercase tracking-wide mb-1">{pt.clause}</p>
                                            <p className="text-[11px] text-[#64748b]"><span className="font-bold">Current:</span> {pt.current}</p>
                                            <p className="text-[11px] text-[#059669] font-bold"><span className="text-[#334155]">Target:</span> {pt.target}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                        {/* Savings Opportunity */}
                        {contract?.savings_opportunity && (
                            <div className="bg-[#eff6ff] border border-[#bfdbfe] rounded-xl p-4 text-[12px] text-[#1e40af] font-medium">
                                <span className="font-black">Savings Opportunity: </span>{contract.savings_opportunity}
                            </div>
                        )}
                    </div>
                );
            case 'hitl_reclaim':
                return (
                    <div className="bg-white rounded-2xl border-[1.5px] border-[#e2e8f0] shadow-sm overflow-hidden mb-6">
                        <div className="bg-red-50 px-5 py-3 border-b border-red-100 flex items-center space-x-2 text-red-600">
                            <AlertTriangle size={16} /> <span className="text-xs font-bold uppercase tracking-widest">400 Dormant Accounts Flagged</span>
                        </div>
                        <div className="p-4">
                            <table className="w-full text-left text-xs">
                                <thead><tr className="text-slate-400 uppercase tracking-wider border-b border-slate-100"><th className="pb-3 pl-2"><CheckSquare size={14} /></th><th className="pb-3">User Email</th><th className="pb-3">Last Active</th><th className="pb-3">Action</th></tr></thead>
                                <tbody className="text-slate-600 font-medium">
                                    {['dev.team@acme.co', 'marketing.bot@acme.co', 'ex.employee@acme.co'].map((e, i) => (
                                        <tr key={i} className="border-b border-slate-50 last:border-0"><td className="py-3 pl-2 text-blue-500"><CheckSquare size={14} /></td><td className="py-3">{e}</td><td className="py-3 text-red-500">&gt; 60 Days</td><td className="py-3 font-bold text-slate-800">REVOKE</td></tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                );
            case 'hitl_email':
                return (
                    <div className="bg-white rounded-2xl border-[1.5px] border-[#e2e8f0] shadow-sm overflow-hidden mb-6">
                        <div className="bg-[#f8fafc] px-5 py-3 border-b border-[#e2e8f0] flex items-center space-x-3">
                            <Mail size={16} className="text-slate-400" /> <span className="text-xs font-bold text-slate-600">Drafted Communication</span>
                        </div>
                        <div className="p-6 text-sm text-slate-700 leading-relaxed">
                            <p className="mb-2"><span className="text-slate-400 font-bold text-xs uppercase">To:</span> renewals@figma.com</p>
                            <p className="mb-4"><span className="text-slate-400 font-bold text-xs uppercase">Subject:</span> Upcoming Renewal - Volume Pricing Requirement</p>
                            <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 italic">
                                "Hi Team, We noticed the upcoming auto-renewal at a 10% increase. Based on our usage audit, we are currently holding 120 unused licenses. We would like to process our renewal keeping the pricing flat, reflecting our continued volume commitment. Please confirm."
                            </div>
                        </div>
                    </div>
                );
            case 'hitl_dpa':
                return (
                    <div className="bg-white rounded-2xl border-[1.5px] border-[#e2e8f0] shadow-sm overflow-hidden mb-6">
                        <div className="bg-emerald-50 px-5 py-3 border-b border-emerald-100 flex items-center space-x-2 text-emerald-700">
                            <ShieldCheck size={16} /> <span className="text-xs font-bold uppercase tracking-widest">DPA Addendum Generated</span>
                        </div>
                        <div className="p-6 text-sm text-slate-700 leading-relaxed font-serif">
                            <h4 className="font-bold text-slate-900 mb-2">ADDENDUM TO DATA PROCESSING AGREEMENT</h4>
                            <p className="mb-4">To address the reported SOC2 sub-processor breach ("CloudData"), Provider agrees to implement the enhanced monitoring protocols outlined in Exhibit A and restricts the transfer of Customer PII to said sub-processor until remediation is verified by an independent auditor.</p>
                        </div>
                    </div>
                );
            default: return null;
        }
    };

    if (view === 'onboarding_wizard') return (
        <OnboardingWizard
            vendorName={onboardingVendor}
            onComplete={() => { setView('dashboard'); setMissionStatus('idle'); }}
            onAbort={() => { setView('dashboard'); setMissionStatus('idle'); setLogs([]); }}
        />
    );

    if (view === 'app_demand') return <DemandPlanningApp onBack={() => setView('dashboard')} />;
    if (view === 'app_vendor') return <VendorIntelligenceApp onBack={() => setView('dashboard')} />;
    if (view === 'app_risk') return <RiskGovernanceApp onBack={() => setView('dashboard')} />;
    if (view === 'app_contract') return <ContractExecutionApp onBack={() => setView('dashboard')} />;

    if (view.startsWith('http')) {
        const activeExternalAgent = ACTIVE_AGENTS.find(a => a.route === view);
        if (activeExternalAgent) {
            return <IframeApp 
                title={activeExternalAgent.name} 
                subtitle={`${activeExternalAgent.pillar}`}
                icon={activeExternalAgent.icon}
                colorClass={activeExternalAgent.color.replace('text-', 'bg-')}
                url={activeExternalAgent.route}
                onBack={() => setView('dashboard')} 
            />;
        }
    }

    return (
        <div className="flex h-screen bg-[#f8fafc] font-sans text-slate-900 overflow-hidden selection:bg-blue-200">
            {/* Sidebar - Rail */}
            <aside className="w-16 flex flex-col items-center py-6 bg-white border-r border-slate-200 z-50 shadow-sm">
                <div 
                    onClick={() => { setView('dashboard'); setMissionStatus('idle'); setLogs([]); }} 
                    className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center shadow-lg cursor-pointer transition-all hover:scale-110 active:scale-95 group relative"
                    title="Main Menu"
                >
                    <LayoutDashboard className="text-white" size={22} />
                    <div className="absolute left-14 bg-slate-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none font-bold uppercase tracking-widest">
                        Main Menu
                    </div>
                </div>
            </aside>

            <main className="flex-1 flex flex-col overflow-hidden">


                <div className="flex-1 flex overflow-hidden relative">
                    {/* Panel Toggles (Floating) */}
                    {!leftPanelVisible && (
                        <button 
                            onClick={() => setLeftPanelVisible(true)}
                            className="absolute left-4 top-4 z-40 p-2 bg-white border border-slate-200 rounded-xl shadow-md hover:bg-slate-50 transition-all text-slate-400 hover:text-blue-600"
                            title="Show Sentinel Feed"
                        >
                            <ChevronRight size={20} />
                        </button>
                    )}
                    {!rightPanelVisible && (
                        <button 
                            onClick={() => setRightPanelVisible(true)}
                            className="absolute right-4 top-4 z-40 p-2 bg-white border border-slate-200 rounded-xl shadow-md hover:bg-slate-50 transition-all text-slate-400 hover:text-blue-600"
                            title="Show Reasoning Engine"
                        >
                            <ChevronLeft size={20} />
                        </button>
                    )}

                    {/* Left Panel: Feed & Controller */}
                    <section className={`${leftPanelVisible ? 'w-[360px]' : 'w-0 overflow-hidden'} border-r border-slate-200 bg-white p-7 flex flex-col z-30 shadow-sm overflow-y-auto transition-all duration-300 relative`}>
                        {leftPanelVisible && (
                            <button 
                                onClick={() => setLeftPanelVisible(false)}
                                className="absolute right-4 top-7 p-1 hover:bg-slate-100 rounded-lg text-slate-300 hover:text-slate-600 transition-colors"
                            >
                                <ChevronLeft size={18} />
                            </button>
                        )}
                        {/* Live Sentinel Alerts */}
                        <div className="mb-8 space-y-4">
                            <h2 className="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] px-1 flex items-center space-x-2">
                                <BellRing size={14} className="text-blue-600" /> <span>Live Sentinel Feed</span>
                            </h2>
                            <div className="space-y-3">
                                {SENTINEL_ALERTS.map(alert => {
                                    const AlertIcon = alert.icon;
                                    return (
                                        <div
                                            key={alert.id}
                                            onClick={() => handleAlertClick(alert)}
                                            className="p-4 rounded-2xl border border-slate-100 bg-white shadow-sm hover:shadow-md hover:border-blue-200 cursor-pointer transition-all group relative overflow-hidden"
                                        >
                                            {activeMissionKey === alert.id && <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500"></div>}
                                            <div className="flex items-center space-x-3 mb-2">
                                                <div className={`p-1.5 rounded-lg ${alert.bg} ${alert.color}`}>
                                                    <AlertIcon size={14} />
                                                </div>
                                                <span className="text-[10px] font-black uppercase text-slate-400 tracking-widest">{alert.agent}</span>
                                            </div>
                                            <h4 className="text-xs font-black text-slate-800 mb-1 group-hover:text-blue-600 transition-colors">{alert.msg}</h4>
                                            <p className="text-[10px] text-slate-500 font-bold leading-tight">{alert.detail}</p>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        <div className="flex-1 space-y-6">
                            <h2 className="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] px-1">Mission Controller</h2>
                            <div onClick={handleNewOnboarding} className={`p-5 rounded-3xl border transition-all cursor-pointer bg-white ${activeMissionKey === 'onboarding' ? 'border-amber-400 ring-4 ring-amber-50 shadow-xl' : 'border-slate-100 hover:border-slate-300'}`}>
                                <div className="flex justify-between items-center mb-2"><span className="text-[10px] font-black text-amber-500 uppercase tracking-[0.1em]">New Onboarding</span><Plus size={18} className="text-amber-500" /></div>
                                <h3 className="text-sm font-black text-slate-800">Launch Lifecycle Discovery</h3>
                            </div>
                        </div>
                    </section>

                    {/* Center Workspace */}
                    <section className="flex-1 p-12 overflow-y-auto bg-slate-50 relative flex justify-center">

                        {view === 'dashboard' && (
                            <div className="w-full max-w-5xl animate-in fade-in">
                                <header className="flex justify-between items-center mb-16">
                                    <div>
                                        <h1 className="text-5xl font-black text-slate-800 tracking-tighter uppercase">Strategic Sourcing</h1>
                                        <p className="text-lg text-blue-600 font-black mt-1 uppercase tracking-[0.3em]">Command Center</p>
                                    </div>
                                </header>

                                <div className="grid grid-cols-3 gap-6 pb-20">
                                    {ACTIVE_AGENTS.map((agent) => {
                                        const AgentIcon = agent.icon;
                                        return (
                                            <div key={agent.id} className="group relative bg-white p-10 rounded-[3rem] border border-slate-100 shadow-sm hover:shadow-2xl transition-all cursor-pointer" onClick={() => agent.route === 'onboarding' ? handleNewOnboarding() : setView(agent.route)}>
                                                <div className="absolute top-8 right-10 flex space-x-2"><Radio size={14} className="text-emerald-500 animate-pulse" /></div>
                                                <div className={`p-5 rounded-3xl shadow-inner mb-8 w-fit ${agent.bg} ${agent.color} shadow-lg transition-transform group-hover:rotate-6`}>
                                                    <AgentIcon size={40} />
                                                </div>
                                                <h4 className="text-[11px] font-black text-slate-400 uppercase tracking-[0.2em] mb-2">{agent.pillar}</h4>
                                                <h3 className="font-black text-slate-800 text-2xl mb-4">{agent.name}</h3>
                                                <div className="mt-8 pt-6 border-t border-slate-50 flex items-center justify-between group/link">
                                                    <div className="flex items-center space-x-3 text-[11px] font-black text-blue-600 uppercase tracking-[0.1em]"><Zap size={14} fill="currentColor" /> <span>Explore Intelligence</span></div>
                                                    <div className="p-2 bg-slate-50 text-slate-300 rounded-xl group-hover/link:bg-blue-600 group-hover/link:text-white transition-all shadow-sm"><ArrowUpRight size={18} /></div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {/* DYNAMIC AGENTIC SOURCING PIPELINE VIEW */}
                        {view === 'active_mission' && currentBlueprint && (
                            <div className="w-full max-w-[800px] animate-in fade-in duration-500 pb-20 relative">

                                {/* STAGE: Awaiting Input (Only for Onboarding) */}
                                {missionStatus === 'awaiting_input' && currentBlueprint.needsInput && (
                                    <div className="bg-white rounded-[3rem] shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 p-16 text-center mt-12">
                                        <input
                                            value={onboardingVendor}
                                            onChange={(e) => setOnboardingVendor(e.target.value)}
                                            className="text-6xl font-black text-slate-800 tracking-tighter lowercase text-center outline-none border-b-2 border-slate-200 focus:border-blue-500 pb-2 bg-transparent w-full"
                                            placeholder="vendor name"
                                        />
                                        <p className="text-[10px] font-black text-slate-400 tracking-[0.3em] uppercase mt-6 mb-16">Agentic Sourcing Pipeline</p>
                                        <button onClick={startBlueprint} disabled={!onboardingVendor.trim()} className="bg-blue-600 hover:bg-blue-700 text-white px-10 py-4 rounded-2xl font-black transition-colors shadow-lg shadow-blue-200 text-sm tracking-widest uppercase disabled:opacity-50 disabled:cursor-not-allowed">
                                            Initialize Discovery
                                        </button>
                                    </div>
                                )}

                                {/* STAGE: Planning (Blueprint Card) */}
                                {missionStatus === 'planning' && (
                                    <div className="bg-white rounded-[2.5rem] shadow-xl border-[1.5px] border-blue-100 overflow-hidden relative max-w-[500px] mx-auto mt-12 animate-in slide-in-from-bottom-8">
                                        <div className={`absolute top-0 right-6 ${currentBlueprint.color} text-white px-6 py-3 rounded-b-xl flex items-center space-x-2 shadow-md z-10`}>
                                            <Target size={14} />
                                            <span className="text-[10px] font-black tracking-[0.15em] uppercase">Mission Blueprint</span>
                                        </div>

                                        <div className="p-10 pb-8 relative z-0">
                                            <h2 className="text-3xl font-black text-[#1e293b] tracking-tight mb-10 capitalize">{currentBlueprint.title}: {onboardingVendor}</h2>
                                            <div className="space-y-6">
                                                {currentBlueprint.steps.map((step, i) => (
                                                    <div key={i} className="flex items-center space-x-6">
                                                        <div className="w-10 h-10 rounded-full bg-[#eff6ff] text-[#2563eb] flex items-center justify-center font-black text-sm border border-[#bfdbfe]">{i + 1}</div>
                                                        <span className="text-[#334155] font-bold text-sm tracking-wide">{step.title} {step.type.startsWith('hitl_') && '(HITL Required)'}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                        <div className="px-10 pb-10">
                                            <button onClick={launchMission} className="w-full bg-[#2563eb] hover:bg-[#1d4ed8] text-white py-5 rounded-2xl font-black flex items-center justify-center space-x-3 transition-colors shadow-lg shadow-blue-200">
                                                <Play size={18} fill="currentColor" />
                                                <span className="text-xs tracking-[0.15em] uppercase">Launch Active Mission</span>
                                            </button>
                                        </div>
                                    </div>
                                )}

                                {/* STAGE: Pipeline Execution */}
                                {['running', 'hitl', 'decision_terminal', 'completed'].includes(missionStatus) && (
                                    <div className="bg-white rounded-[3rem] shadow-[0_8px_30px_rgb(0,0,0,0.04)] border-[3px] border-[#fdfbf7] p-10 pt-16 relative mt-12">

                                        {/* Dynamic Track Pill */}
                                        <div className={`absolute top-0 right-10 transform -translate-y-[2px] ${currentBlueprint.color} text-white px-6 py-3 rounded-b-xl text-[10px] font-black uppercase flex items-center space-x-2 shadow-lg z-20`}>
                                            <currentBlueprint.icon size={14} /><span>Track: {currentBlueprint.track}</span>
                                        </div>

                                        {/* Header Section */}
                                        <div className="text-center mb-12">
                                            <h2 className="text-5xl font-black text-[#1e293b] tracking-tighter lowercase">{onboardingVendor}</h2>
                                            <p className="text-[10px] font-black text-[#94a3b8] tracking-[0.3em] uppercase mt-3">Agentic Pipeline: {currentBlueprint.title}</p>
                                        </div>

                                        {/* The Workflow Steps Container */}
                                        <div className="space-y-4 max-w-[650px] mx-auto">
                                            {currentBlueprint.steps.map((step, i) => {
                                                const isComplete = completedSteps.includes(i);
                                                const isActive = currentStepIndex === i;
                                                const isHitlPending = isActive && missionStatus === 'hitl';

                                                if (currentStepIndex < i && !isComplete) return null; // Hide future steps

                                                return (
                                                    <div key={i} className={`rounded-3xl border-[1.5px] transition-all duration-500 overflow-hidden ${isComplete ? 'border-[#a7f3d0] bg-[#f0fdf4] shadow-sm' : isActive ? 'border-[#3b82f6] bg-white shadow-xl ring-[6px] ring-[#eff6ff]' : 'border-slate-100 bg-white opacity-50'}`}>

                                                        {/* Header */}
                                                        <div className="p-6 flex items-center justify-between bg-white relative z-10 rounded-3xl">
                                                            <div className="flex items-center space-x-5">
                                                                <div className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-colors ${isComplete ? 'bg-[#10b981] text-white shadow-md' : isActive ? 'bg-[#3b82f6] text-white shadow-md' : 'bg-slate-100 text-slate-400'}`}>
                                                                    <step.icon size={24} strokeWidth={2.5} />
                                                                </div>
                                                                <div>
                                                                    <h4 className="font-black text-[15px] tracking-wide mb-1 text-[#0f172a] uppercase">{step.title}</h4>
                                                                    <p className={`text-[10px] font-black uppercase tracking-[0.15em] ${isComplete ? 'text-[#10b981]' : isActive && !isHitlPending ? 'text-[#3b82f6] animate-pulse' : isActive && isHitlPending ? 'text-amber-500' : 'text-slate-400'}`}>
                                                                        {isComplete ? 'Stage Verified' : isActive && !isHitlPending ? 'Agent Analyzing...' : isHitlPending ? 'Action Required' : 'Pending'}
                                                                    </p>
                                                                </div>
                                                            </div>
                                                            <div className="flex items-center space-x-4 text-slate-300 pr-2">
                                                                {isComplete && <div className="w-6 h-6 rounded-full bg-[#10b981] flex items-center justify-center"><Check size={14} strokeWidth={4} className="text-white" /></div>}
                                                                {isActive && !isHitlPending && <Loader2 size={24} className="text-[#3b82f6] animate-spin" />}
                                                                {isHitlPending && <div className="w-6 h-6 rounded-full border-[3px] border-amber-500 border-t-transparent animate-spin"></div>}
                                                                <ChevronDown size={20} className={isHitlPending ? "transform rotate-180 text-slate-300" : "text-slate-300"} />
                                                            </div>
                                                        </div>

                                                        {/* Expanded Content View (Auto Logs or HITL UI) */}
                                                        {isActive && !isHitlPending && (
                                                            <div className="px-8 pb-8 pt-2 bg-white animate-in slide-in-from-top-4">
                                                                <p className="text-[11px] font-black text-[#94a3b8] uppercase tracking-widest italic">{step.log}</p>
                                                            </div>
                                                        )}

                                                        {isComplete && (
                                                            <div className="px-8 pb-8 bg-[#f0fdf4] rounded-b-3xl">
                                                                <p className="text-[11px] font-black text-[#94a3b8] uppercase tracking-widest mb-4 mt-2 italic">{step.log}</p>
                                                            </div>
                                                        )}

                                                        {isHitlPending && (
                                                            <div className="px-8 pb-8 pt-2 bg-white animate-in slide-in-from-top-4 border-t border-slate-50">
                                                                <p className="text-[11px] font-black text-[#94a3b8] uppercase tracking-widest mb-4 italic mt-4">{step.log}</p>

                                                                {/* Dynamic Content based on HITL Type */}
                                                                {renderHitlContent(step.type)}

                                                                <div className="flex space-x-4 mt-4">
                                                                    <button onClick={handleHitlApproval} className="flex-[3] bg-[#2563eb] hover:bg-[#1d4ed8] text-white py-4 rounded-2xl font-black text-xs tracking-widest uppercase transition-colors shadow-lg">
                                                                        Approve & Proceed
                                                                    </button>
                                                                    <button className="flex-[2] bg-[#f8fafc] text-[#64748b] border border-[#e2e8f0] py-4 rounded-2xl font-black text-xs tracking-widest uppercase hover:bg-[#f1f5f9] transition-colors">
                                                                        Modify
                                                                    </button>
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                );
                                            })}

                                            {/* --- DECISION TERMINAL --- */}
                                            {(missionStatus === 'decision_terminal' || missionStatus === 'completed') && (
                                                <div className="bg-[#0f172a] rounded-[2.5rem] shadow-2xl p-10 pt-12 relative overflow-hidden mt-8 animate-in slide-in-from-bottom-8 border border-[#1e293b]">
                                                    <div className="absolute top-0 right-0 w-64 h-64 bg-[#10b981] rounded-full blur-[100px] opacity-10 pointer-events-none"></div>

                                                    <div className="flex items-center space-x-4 mb-8">
                                                        <div className="w-14 h-14 rounded-2xl bg-[#10b981] text-white flex items-center justify-center shadow-[0_0_20px_rgba(16,185,129,0.3)]">
                                                            <currentBlueprint.icon size={28} strokeWidth={2} />
                                                        </div>
                                                        <div>
                                                            <h3 className="text-white font-black text-xl tracking-wide uppercase">Decision Terminal</h3>
                                                            <p className="text-[#10b981] text-[10px] font-black uppercase tracking-[0.2em] mt-1">Final Lifecycle Approval</p>
                                                        </div>
                                                    </div>

                                                    <div className="bg-[#1e293b] rounded-2xl p-5 mb-5 border border-[#334155] flex items-center space-x-4">
                                                        <Scale size={20} className="text-[#10b981]" />
                                                        <span className="text-white font-black text-sm">System Verdict: <span className={sessionData?.verdict?.verdict === 'NO_GO' ? 'text-[#ef4444]' : sessionData?.verdict?.verdict === 'CONDITIONAL_GO' ? 'text-[#f59e0b]' : 'text-[#10b981]'}>{sessionData?.verdict?.verdict || currentBlueprint.verdict}</span></span>
                                                    </div>

                                                    {/* Real risk + savings data from backend */}
                                                    {sessionData?.verdict && (
                                                        <div className="grid grid-cols-3 gap-3 mb-5">
                                                            <div className="bg-[#1e293b] rounded-xl p-4 border border-[#334155] text-center">
                                                                <p className="text-[#64748b] text-[10px] uppercase tracking-widest mb-1">Risk Score</p>
                                                                <p className="text-white font-black text-lg">{sessionData?.risk?.score ?? '—'}<span className="text-[#64748b] text-xs">/10</span></p>
                                                            </div>
                                                            <div className="bg-[#1e293b] rounded-xl p-4 border border-[#334155] text-center">
                                                                <p className="text-[#64748b] text-[10px] uppercase tracking-widest mb-1">Risk Level</p>
                                                                <p className={`font-black text-sm ${sessionData?.risk?.level === 'HIGH' ? 'text-[#ef4444]' : sessionData?.risk?.level === 'MEDIUM' ? 'text-[#f59e0b]' : 'text-[#10b981]'}`}>{sessionData?.risk?.level ?? '—'}</p>
                                                            </div>
                                                            <div className="bg-[#1e293b] rounded-xl p-4 border border-[#334155] text-center">
                                                                <p className="text-[#64748b] text-[10px] uppercase tracking-widest mb-1">Security</p>
                                                                <p className="text-white font-black text-lg">{sessionData?.risk?.security_rating ?? '—'}</p>
                                                            </div>
                                                        </div>
                                                    )}

                                                    <div className="bg-[#1e293b] rounded-2xl p-6 mb-8 border border-[#334155]">
                                                        <p className="text-[#94a3b8] text-sm font-bold italic leading-relaxed">"{sessionData?.verdict?.summary || currentBlueprint.summary}"</p>
                                                        {sessionData?.contract?.savings_opportunity && (
                                                            <p className="text-[#10b981] text-[11px] font-black uppercase tracking-widest mt-3">{sessionData.contract.savings_opportunity}</p>
                                                        )}
                                                    </div>

                                                    {missionStatus === 'decision_terminal' ? (
                                                        <div className="flex space-x-5">
                                                            <button onClick={handleConfirmMission} className="flex-[3] bg-[#047857] hover:bg-[#065f46] text-white py-5 rounded-2xl font-black text-xs tracking-[0.2em] uppercase transition-colors shadow-[0_0_15px_rgba(4,120,87,0.4)] flex items-center justify-center space-x-3">
                                                                <CheckCircle2 size={18} /> <span>Confirm Execution</span>
                                                            </button>
                                                        </div>
                                                    ) : (
                                                        <div className="flex flex-col space-y-4">
                                                            <div className="bg-[#064e3b] border border-[#047857] text-white py-5 rounded-2xl font-black text-xs tracking-widest uppercase flex items-center justify-center space-x-3">
                                                                <CheckCircle2 size={18} /> <span>Mission Accomplished</span>
                                                            </div>
                                                            <button
                                                                onClick={() => { setView('dashboard'); setMissionStatus('idle'); setLogs([]); }}
                                                                className="w-full bg-[#1e293b] hover:bg-[#334155] text-white py-4 rounded-2xl font-black text-xs tracking-[0.1em] uppercase transition-colors shadow-lg flex items-center justify-center space-x-2"
                                                            >
                                                                <span>Return to Strategic Sourcing Command Center</span> <ChevronRight size={16} />
                                                            </button>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </section>

                    {/* Right Panel: Reasoning Engine */}
                    <section className={`${rightPanelVisible ? 'w-[420px]' : 'w-0 overflow-hidden'} border-l border-slate-200 bg-white flex flex-col z-30 shadow-sm relative transition-all duration-300`}>
                        {rightPanelVisible && (
                            <button 
                                onClick={() => setRightPanelVisible(false)}
                                className="absolute left-4 top-8 p-1 hover:bg-slate-100 rounded-lg text-slate-300 hover:text-slate-600 transition-colors z-50"
                            >
                                <ChevronRight size={18} />
                            </button>
                        )}
                        <div className="p-8 border-b border-slate-100 flex justify-between items-center bg-white font-black text-[11px] uppercase tracking-[0.25em]">Reasoning Engine</div>

                        <div ref={pulseRef} className="flex-1 p-8 overflow-y-auto space-y-10 scroll-smooth relative bg-slate-50/50">
                            <div className="absolute left-[3.25rem] top-8 bottom-8 w-[2px] bg-slate-200 opacity-60"></div>

                            {logs.length === 0 && (
                                <div className="h-full flex flex-col items-center justify-center text-center px-10 opacity-30">
                                    <div className="p-10 bg-white rounded-[3rem] mb-6 border-4 border-dashed border-slate-200"><BrainCircuit size={60} className="text-slate-300" /></div>
                                    <p className="text-sm font-black text-slate-400 tracking-widest uppercase">System Feed Dormant</p>
                                </div>
                            )}

                            {logs.map((log, i) => (
                                <div key={i} className="relative pl-16 animate-in fade-in slide-in-from-right-10 duration-700">
                                    <div className={`absolute left-0 top-0 w-12 h-12 rounded-2xl border-[3px] border-white z-20 flex items-center justify-center shadow-md bg-[#0f172a] text-white`}><Target size={20} strokeWidth={2.5} /></div>
                                    <div className="bg-white p-6 rounded-[1.5rem] border border-slate-100 shadow-sm hover:shadow-md transition-all space-y-4">
                                        <div className="flex justify-between items-start">
                                            <p className="text-sm text-slate-800 font-bold leading-snug">{log.msg}</p>
                                            <span className="text-[8px] font-black uppercase tracking-widest bg-blue-50 text-blue-600 px-2 py-1 rounded-md ml-4 whitespace-nowrap border border-blue-100">
                                                {log.agent}
                                            </span>
                                        </div>
                                        <div className="pt-3 border-t border-slate-50">
                                            <div className="flex items-center space-x-2 text-[10px] text-slate-400 font-black uppercase tracking-[0.1em] mb-2"><Info size={14} /> <span>Logic Chain</span></div>
                                            <p className="text-[11px] text-slate-500 italic font-medium leading-relaxed bg-slate-50 p-4 rounded-xl border border-slate-100/50">{log.reason}</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Sticky HITL Warning Footer */}
                        {missionStatus === 'hitl' && (
                            <div className="p-6 border-t-[3px] border-[#f59e0b] bg-[#fffbeb] flex items-center justify-center space-x-3 text-[#d97706] z-40 animate-in slide-in-from-bottom-full">
                                <AlertCircle size={20} strokeWidth={2.5} className="animate-bounce" />
                                <span className="text-[11px] font-black uppercase tracking-[0.2em]">HITL Decision Pending</span>
                            </div>
                        )}
                    </section>
                </div>
            </main>
        </div>
    );
};

export default App;