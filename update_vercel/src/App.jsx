import React, { useState } from 'react';
import {
    Brain,
    Calendar,
    CheckCircle2,
    Cpu,
    Database,
    LayoutDashboard,
    Lightbulb,
    Rocket,
    Zap,
    ArrowRight,
    ShieldAlert,
    TrendingUp,
    Layers,
    Search,
    PieChart,
    Mail,
    FileJson,
    ShieldCheck,
    History,
    Terminal,
    Settings,
    Bell,
    Grid,
    ChevronRight,
    Info,
    User,
    Server,
    FileText,
    MessageSquare,
    ChevronRightSquare,
    MousePointer2,
    FileSpreadsheet,
    AlertTriangle,
    ClipboardCheck,
    CheckCircle,
    XCircle,
    Clock,
    ArrowDown,
    FileDown,
    Table
} from 'lucide-react';

// --- Data Constants ---

const DPE_TIMELINE_DATA = {
    "February 2026": [
        { task: "Initial Scoping & Requirement Gathering", status: "completed", category: "Planning" },
        { task: "Demand Source Identification", status: "completed", category: "Data" }
    ],
    "March 2026": [
        { task: "Data Schema Design", status: "completed", category: "Design" },
        { task: "Backend Infrastructure Setup", status: "completed", category: "Infra" }
    ],
    "April 2026": [
        { task: "Multi-intent Detection (Forecast, Budget, Savings)", status: "completed", category: "AI" },
        { task: "Demand Forecasting & Budget Engine", status: "completed", category: "Core" },
        { task: "Case 2: Strategic Sourcing Workspace UI", status: "completed", category: "Frontend" },
        { task: "Semantic Role-to-Tier Matching (Generated Data)", status: "completed", category: "AI" },
        { task: "Streamlit + Plotly Dashboard Implementation", status: "completed", category: "Frontend" },
        { task: "CSV/SQL Backend Integration", status: "completed", category: "Data" },
        { task: "One-Click Procurement Report Generation", status: "completed", category: "Export" }
    ],
    "May 2026": [
        { task: "Integration with Live HR Data Systems", status: "planned", category: "Data" },
        { task: "Dynamic Role Description Libraries", status: "planned", category: "Context" },
        { task: "Department-specific Mapping Libraries", status: "planned", category: "Context" },
        { task: "Advanced Agentic Context-Role Mapping", status: "planned", category: "AI" },
        { task: "Continuous Market Benchmark Sync", status: "planned", category: "Integration" }
    ]
};

const NEGOTIATION_TIMELINE_DATA = {
    "February 2026": [
        { task: "Initial System Integration", status: "completed", category: "Core" },
        { task: "Prompt Optimization for Llama", status: "completed", category: "AI" }
    ],
    "March 2026": [
        { task: "High-volume Pipeline Optimization", status: "planned", category: "Scalability" },
        { task: "Compliance & Audit Logs", status: "planned", category: "Governance" },
        { task: "Deployment & Monitoring", status: "planned", category: "Ops" }
    ],
    "April 2026": [
        { task: "Tavily API integration completed", status: "completed", category: "Integration" },
        { task: "Earnings Call API", status: "completed", category: "Data" },
        { task: "Daily/Weekly Ingestion Pipelines", status: "testing", category: "Automation" },
        { task: "Refine Dashboard", status: "completed", category: "Frontend" },
        { task: "Testing", status: "planned", category: "QA" }
    ],
    "May 2026": [
        { task: "Full Production Rollout", status: "planned", category: "Milestone" },
        { task: "Global User Training", status: "planned", category: "Ops" }
    ]
};

const CRA_TIMELINE_DATA = {
    "January 2026": [
        { task: "CRA Scoping & Requirement Gathering", status: "completed", category: "Planning" },
        { task: "Identify Tier-0 Vendors for Pilot", status: "completed", category: "Strategy" },
        { task: "Architecture Design for License Ingestion", status: "completed", category: "Design" },
        { task: "Data Source Mapping (Workday/Flexera/ERP)", status: "completed", category: "Data" }
    ],
    "February 2026": [
        { task: "MVP - prototype on Lucid and Figma", status: "completed", category: "Milestone" },
        { task: "ENV setup & techstack accesses", status: "completed", category: "Infra" },
        { task: "Headcount data notebook integration", status: "in-progress", category: "Data" },
        { task: "Flexera backend tables accessed", status: "in-progress", category: "Data" }
    ],
    "March 2026": [
        { task: "5-stage contract renewal workflow implemented", status: "completed", category: "Milestones" },
        { task: "End-to-end automation from planning to closure", status: "completed", category: "Milestones" },
        { task: "Renewal recommendations engine developed", status: "completed", category: "Milestones" },
        { task: "Backend services built using FastAPI", status: "completed", category: "Infrastructure" },
        { task: "Stateful agent logic for workflow tracking", status: "completed", category: "Infrastructure" },
        { task: "Dashboard setup for real-time monitoring", status: "completed", category: "Infrastructure" }
    ],
    "April 2026": [
        { task: "Contract utilization and budget tracking enabled", status: "completed", category: "Data" },
        { task: "True-up exposure and risk analysis implemented", status: "completed", category: "Data" },
        { task: "Spend forecasting and historical analysis integrated", status: "completed", category: "Data" }
    ]
};

const VENDOR_GUARD_TIMELINE_DATA = {
    "February 2026": [
        { task: "Project Initiation & Core Foundation", status: "completed", category: "Foundation" },
        { task: "Project Initiation", status: "completed", category: "Planning" },
        { task: "Architecture Design", status: "completed", category: "Design" },
        { task: "Tech Stack Selection", status: "completed", category: "Infra" },
        { task: "Vendor Schema Setup", status: "completed", category: "Data" },
        { task: "Risk Framework Planning", status: "completed", category: "Strategy" }
    ],
    "March 2026": [
        { task: "Core Backend & AI Intelligence Development", status: "completed", category: "Development" },
        { task: "Backend Development", status: "completed", category: "Backend" },
        { task: "Flask APIs", status: "completed", category: "API" },
        { task: "Vendor Alert Engine", status: "completed", category: "Core" },
        { task: "AI/LLM Integration", status: "completed", category: "AI" },
        { task: "Risk Classification", status: "completed", category: "Logic" },
        { task: "Excel Storage", status: "completed", category: "Data" }
    ],
    "April 2026": [
        { task: "Workflow Automation & Dashboard Development", status: "completed", category: "Automation" },
        { task: "Dashboard Development", status: "completed", category: "Frontend" },
        { task: "Approval/Rejection Workflow", status: "completed", category: "Workflow" },
        { task: "Jira Integration", status: "completed", category: "Integration" },
        { task: "Gmail Automation", status: "completed", category: "Automation" },
        { task: "Status Tracking", status: "completed", category: "Tracking" },
        { task: "Reporting System", status: "completed", category: "Reporting" }
    ],
    "May 2026": [
        { task: "UI Optimization & Operational Refinement", status: "in-progress", category: "Refinement" },
        { task: "UI/UX Refinement", status: "in-progress", category: "Design" },
        { task: "Vendor Sidebar", status: "in-progress", category: "Frontend" },
        { task: "Dashboard Optimization", status: "in-progress", category: "Optimization" },
        { task: "Analytics Improvements", status: "planned", category: "Analytics" },
        { task: "Workflow Enhancements", status: "planned", category: "Workflow" }
    ],
    "Enterprise Enhancements": [
        { task: "Planned Enterprise Enhancements", status: "planned", category: "Future" }
    ]
};

const DPE_PHASE_1_DETAILS = [
    { tech: "Multi-turn Conversational Agent for Intent Routing", impact: "Accurately routes requests between Existing Vendor (Case 1) and Net-New (Case 2)" },
    { tech: "Semantic Role-to-Tier Matching using LLMs", impact: "Assigns license tiers based on job descriptions without historical data" },
    { tech: "Unified Filter Architecture (Streamlit)", impact: "Single filter state drives all KPIs and live workspace charts simultaneously" },
    { tech: "Simulated Data Layer (hr_data_v1, vendor_catalog)", impact: "Validates the sourcing and buffer-check logic in a controlled prototype environment" },
    { tech: "Implemented Agents for Summarizing Quarterly Reports and Sharing with Respective Users via Email", impact: "Automates generation and distribution of quarterly insights to stakeholders, improving visibility and reducing manual reporting effort" }
];

const DPE_PHASE_2_DETAILS = [
    { tech: "Live HR Data Pipeline Integration", impact: "Replaces CSV simulations with real-time employee and future-hire data" },
    { tech: "Role & Department Context Libraries", impact: "Creates a scalable, dynamic context engine for hyper-accurate semantic matching" },
    { tech: "Planned: Agentic Intelligence Layer for Safer, More Accurate Mapping & Demand Discovery", impact: "Introduces an initial demand discovery agent and report generation based on user selections. Enhances mapping accuracy and decision confidence through agent-driven intelligence layer." }
];

const NEGOTIATION_PHASE_1_DETAILS = [
    { tech: "Unified Vendor Intelligence Framework", impact: "Consistent and structured vendor intelligence for QBRs" },
    { tech: "Earnings & Strategy Agent", impact: "Reliable signal extraction for strategic decision-making" },
    { tech: "Prompt frameworks for pricing and commercial signal detection", impact: "Supports structured analysis of pricing and commercial trends" },
    { tech: "Tavily Search API Implementation", impact: "Provides real-time grounding for vendor intelligence agents" },
    { tech: "Agentic Layer Implemented (Briefing, Summary, Chatbot, Earnings, QBR, Search)", impact: "Enables multi-agent collaboration for automated briefings and summarized intelligence outputs" }
];

const CRA_PHASE_1_DETAILS = [
    { tech: "Automated 5-stage workflow", impact: "Provides a strict, audit-ready record of every contract journey" },
    { tech: "Role-Based Action Routing & HTML Emails", impact: "Stakeholders receive analysis and action buttons directly in their inbox" },
    { tech: "Standalone AI Contract Intelligence", impact: "Generates document summaries separately using ADK and Langchain" },
    { tech: "Streamlit Live Dashboard", impact: "Real-time visibility into KPIs, at-risk contracts, and stage tracking" },
    { tech: "CRA Summarizer Agent", impact: "Analyzes contracts during planning phase to provide consolidated demand overviews" }
];

const CRA_PHASE_2_DETAILS = [
    { tech: "Fully Agentic Workflow Orchestration", impact: "Shifts from linear logic to an intelligent, reasoning-based autonomous agent" },
    { tech: "Unified Core Agent Integration", impact: "Merges the standalone document summarizer directly into the agent's action loop" },
    { tech: "Planned: Specialized Agents (Budgeting, Approver)", impact: "Multi-agent system handling decision layers across the renewal lifecycle" }
];

const VG_PHASE_1_DETAILS = [
    { tech: "Project Initiation & Core Foundation", impact: "Baseline infrastructure and scope finalized for vendor risk intelligence" },
    { tech: "Core Backend & AI Intelligence Development", impact: "Flask backend and risk classification engines operational" },
    { tech: "Agentic Layer (Financial, Compliance, Cyber, Legal)", impact: "Enables multi-dimensional risk evaluation across critical domains" }
];

const VG_PHASE_2_DETAILS = [
    { tech: "Workflow Automation & Dashboard Development", impact: "Remediation pipelines and real-time monitoring enabled" },
    { tech: "UI Optimization & Operational Refinement", impact: "Refined navigation and UX for enterprise stakeholders" },
    { tech: "Expansion of agentic remediation", impact: "Specialized agents driving deeper insights and proactive alerts" }
];

// --- Enterprise UI Components ---

const StatusBadge = ({ status }) => {
    const styles = {
        completed: "bg-teal-50 text-teal-700 border-teal-200",
        "in-progress": "bg-blue-50 text-blue-700 border-blue-200",
        pending: "bg-amber-50 text-amber-700 border-blue-200",
        planned: "bg-slate-50 text-slate-600 border-slate-200",
        testing: "bg-indigo-50 text-indigo-700 border-indigo-200"
    };
    const labels = {
        completed: "ACHIEVED",
        "in-progress": "IN PROGRESS",
        pending: "PENDING",
        planned: "PLANNED",
        testing: "TESTING"
    };
    return (
        <span className= {`px-2 py-0.5 rounded-sm text-[10px] font-bold tracking-wider border ${styles[status] || styles.planned}`
}>
    { labels[status] || status }
    </span>
  );
};

const Card = ({ children, className = "" }) => (
    <div className= {`bg-white rounded-xl border border-slate-200 shadow-sm ${className}`}>
        { children }
        </div>
);

// --- Architecture Diagram Components ---

const DemandEngineArchitectureDiagram = () => (
    <div className= "w-full bg-[#fdfdfd] border border-slate-200 rounded-xl p-6 overflow-x-auto" >
    <div className="min-w-[1100px] flex flex-col items-center" >

        {/* Input Layer */ }
        < div className = "flex items-center gap-12 mb-8" >
            <div className="p-3 border border-slate-300 rounded-lg bg-white shadow-sm flex flex-col items-center w-40 text-center" >
                <User className="w-5 h-5 text-slate-700 mb-1" />
                    <span className="text-[10px] font-bold text-slate-900" > Sourcing Manager </span>
                        </div>
                        < div className = "flex items-center gap-3" >
                            <div className="h-px w-10 bg-slate-400" > </div>
                                < div className = "text-[9px] text-slate-500 font-bold max-w-[120px] text-center italic" > Chat input(Gradio) or Tableau dashboard filters </div>
                                    < ArrowRight className = "w-4 h-4 text-slate-400" />
                                        </div>
                                        < div className = "p-4 border-2 border-slate-900 rounded-lg bg-white shadow-md flex flex-col items-center w-48 text-center" >
                                            <Cpu className="w-6 h-6 text-slate-900 mb-1" />
                                                <span className="text-[11px] font-bold text-slate-900 leading-tight" > Main Dispatcher </span>
                                                    < span className = "text-[9px] text-slate-500 font-mono" > handle_query + is_case2_sourcing_request </span>
                                                        </div>
                                                        </div>

{/* Main Flow Grid */ }
<div className="grid grid-cols-2 gap-12 w-full px-4" >

    {/* Case 1: Demand Planning Engine */ }
    < div className = "border-2 border-blue-200 rounded-2xl bg-blue-50/20 p-6 flex flex-col gap-6 relative" >
        <div className="flex items-center gap-2 pb-3 border-b border-blue-100" >
            <span className="text-xs font-bold text-blue-900 uppercase tracking-tight" > Case 1 - Demand Planning Engine(Backend) </span>
                </div>

                < div className = "flex flex-col gap-1 items-center -mt-4 mb-2" >
                    <div className="h-6 w-px bg-slate-300 border-dashed border-l" > </div>
                        < span className = "text-[8px] font-bold text-slate-400" > KEYWORDS: forecast, budget, renewal...</span>
                            </div>

                            < div className = "grid grid-cols-3 gap-4" >
                                <div className="p-3 border border-blue-100 rounded bg-white shadow-sm flex flex-col gap-2" >
                                    <span className="text-[9px] font-bold text-blue-800" > 1. Intent Detection </span>
                                        < span className = "text-[8px] text-slate-500 leading-tight" > forecast / budget / renewal / at_risk / savings / mail / overview </span>
                                            </div>
                                            < div className = "p-3 border border-blue-100 rounded bg-white shadow-sm flex flex-col gap-2" >
                                                <span className="text-[9px] font-bold text-blue-800" > 2. Entity Extraction </span>
                                                    < span className = "text-[8px] text-slate-500 leading-tight" > Vendor(with pending session state), month(quarter - aware), splits(dept / role) </span>
                                                        </div>
                                                        < div className = "p-3 border border-blue-100 rounded bg-white shadow-sm flex flex-col gap-2" >
                                                            <span className="text-[9px] font-bold text-blue-800" > 3. Build Context </span>
                                                                < span className = "text-[8px] text-slate-500 leading-tight" > SQL data retrieval + formatting </span>
                                                                    </div>
                                                                    </div>

                                                                    < div className = "flex items-start gap-8 mt-2" >
                                                                        <div className="flex flex-col gap-4" >
                                                                            <div className="p-3 border border-amber-200 rounded-lg bg-amber-50/50" >
                                                                                <span className="text-[9px] font-bold text-amber-800 uppercase block mb-3 border-b border-amber-100 pb-1" > Email Actions </span>
                                                                                    < div className = "flex gap-2" >
                                                                                        <div className="p-2 border border-amber-200 rounded bg-white text-[8px] flex flex-col gap-1" >
                                                                                            <span className="font-bold" > Overview Chip </span>
Generates & sends quarterly report email with SharePoint link
    </div>
    < div className = "p-2 border border-amber-200 rounded bg-white text-[8px] flex flex-col gap-1" >
        <span className="font-bold" > At - Risk Chip </span>
                    Sends Google Form to inactive user
    </div>
    </div>
    </div>
    </div>

    < div className = "flex flex-col items-center gap-3 flex-1 pt-6" >
        <div className="p-3 border border-blue-100 rounded bg-white w-full text-center" >
            <span className="text-[9px] font-bold text-blue-800 block" > 4. Augment LLM Prompt </span>
                < span className = "text-[7px] text-slate-400" > STRICT rules: no hallucination, always show licenses + cost </span>
                    </div>
                    < ArrowDown className = "w-3 h-3 text-slate-300" />
                        <div className="p-2 border border-blue-100 rounded-full bg-blue-50/50 w-12 h-12 flex items-center justify-center font-bold text-[10px] text-blue-900" > 5. LLM </div>
                            < ArrowDown className = "w-3 h-3 text-slate-300" />
                                <div className="p-2 border border-blue-100 rounded bg-white w-full text-center" >
                                    <span className="text-[9px] font-bold text-blue-800 block" > 6. Conversational Response </span>
                                        </div>
                                        </div>
                                        </div>

                                        < div className = "mt-8 border-2 border-blue-200 rounded-xl p-4 bg-white" >
                                            <div className="text-[10px] font-bold text-blue-900 border-b border-blue-50 pb-2 mb-3" > Case 1 - User Interface(Tableau + Gradio Chat) </div>
                                                < div className = "flex gap-4" >
                                                    <div className="flex-1 p-2 bg-slate-50 rounded" >
                                                        <span className="text-[9px] font-bold text-slate-700 block mb-1" > Tableau Dashboard </span>
                                                            < ul className = "text-[8px] text-slate-500 space-y-1" >
                                                                <li>• Total Active Seats </li>
                                                                    <li>• New Demand(2026) </li>
                                                                        <li>• Renewal Pipeline </li>
                                                                            <li>• Reclaimable Savings </li>
                                                                                <li>• Projected Growth Chart </li>
                                                                                    <li>• Renewal Pipeline Chart </li>
                                                                                        <li>• Retention Analysis </li>
                                                                                            </ul>
                                                                                            </div>
                                                                                            < div className = "flex-1 p-2 bg-slate-50 rounded" >
                                                                                                <span className="text-[9px] font-bold text-slate-700 block mb-1" > Floating Chat(Gradio) </span>
                                                                                                    < ul className = "text-[8px] text-slate-500 space-y-1" >
                                                                                                        <li>• Predefined Chips(Forecast, Renewal Split, Churn Users, Overview, Budget) </li>
                                                                                                            <li>• Free - text Q & A </li>
                                                                                                                </ul>
                                                                                                                </div>
                                                                                                                </div>
                                                                                                                </div>
                                                                                                                </div>

{/* Case 2: Demand Discovery Workspace */ }
<div className="border-2 border-green-200 rounded-2xl bg-green-50/20 p-6 flex flex-col gap-4" >
    <div className="flex items-center gap-2 pb-3 border-b border-green-100" >
        <span className="text-xs font-bold text-green-900 uppercase tracking-tight" > Case 2 - Demand Discovery Workspace(Backend) </span>
            </div>

            < div className = "flex flex-col gap-1 items-center -mt-4 mb-2" >
                <div className="h-6 w-px bg-slate-300 border-dashed border-l" > </div>
                    < span className = "text-[8px] font-bold text-slate-400" > KEYWORDS: new vendor, need licenses...</span>
                        </div>

                        < div className = "space-y-3" >
                            <div className="p-3 border border-green-100 rounded bg-white shadow-sm flex flex-col gap-1" >
                                <span className="text-[9px] font-bold text-green-800" > 1. Extract Request </span>
                                    < span className = "text-[8px] text-slate-500" > Vendor, SKU, Tier, Department, Role, Level </span>
                                        </div>
                                        < div className = "p-3 border border-green-100 rounded bg-white shadow-sm flex flex-col gap-1" >
                                            <span className="text-[9px] font-bold text-green-800" > 2. Build Workspace View </span>
                                                < span className = "text-[8px] text-slate-500" > Semantic role - to - tier matching + vendor benchmarks + volume - tiered pricing </span>
                                                    </div>
                                                    < div className = "p-3 border border-green-100 rounded bg-white shadow-sm flex flex-col gap-1" >
                                                        <span className="text-[9px] font-bold text-green-800" > 3. Filter & Aggregate </span>
                                                            < span className = "text-[8px] text-slate-500" > KPIs(demand, spend, delta) Sourcing Insights Negotiation Delta Insight </span>
                                                                </div>
                                                                < div className = "flex items-center gap-4" >
                                                                    <div className="flex-1 p-3 border border-green-100 rounded bg-white shadow-sm flex flex-col gap-1" >
                                                                        <span className="text-[9px] font-bold text-green-800" > 4. Save workspace_context.json </span>
                                                                            </div>
                                                                            < div className = "p-3 border border-pink-200 rounded bg-pink-50/50 flex flex-col gap-1 flex-1" >
                                                                                <span className="text-[9px] font-bold text-pink-800 uppercase" > 5. One - Click Report Generation </span>
                                                                                    < span className = "text-[7px] text-pink-600 font-mono" > build_report_docx_bytes </span>
                                                                                        < span className = "text-[8px] text-slate-500" > Creates downloadable.docx with demand snapshot </span>
                                                                                            </div>
                                                                                            </div>
                                                                                            < div className = "p-3 border border-amber-100 rounded bg-amber-50/30 flex flex-col gap-1 text-center" >
                                                                                                <span className="text-[9px] font-bold text-amber-800" > 6. Initial Summary </span>
                                                                                                    < span className = "text-[8px] text-slate-500" > (link to workspace)</span>
                                                                                                        </div>
                                                                                                        </div>

                                                                                                        < div className = "mt-4 border-2 border-green-200 rounded-xl p-4 bg-white" >
                                                                                                            <div className="text-[10px] font-bold text-green-900 border-b border-green-50 pb-2 mb-3" > Case 2 - User Interface(Streamlit Workspace) </div>
                                                                                                                < div className = "grid grid-cols-5 gap-2" >
                                                                                                                    <div className="p-1.5 border border-slate-100 rounded text-center" >
                                                                                                                        <span className="text-[8px] font-bold block mb-1" > Sidebar Filters </span>
                                                                                                                            < span className = "text-[7px] text-slate-400" > Vendor, Dept, License, Role </span>
                                                                                                                                </div>
                                                                                                                                < div className = "p-1.5 border border-slate-100 rounded text-center" >
                                                                                                                                    <span className="text-[8px] font-bold block mb-1" > KPI Header </span>
                                                                                                                                        < span className = "text-[7px] text-slate-400" > Demand, Cost, Spend, Delta </span>
                                                                                                                                            </div>
                                                                                                                                            < div className = "p-1.5 border border-slate-100 rounded text-center" >
                                                                                                                                                <span className="text-[8px] font-bold block mb-1" > Sourcing Insights </span>
                                                                                                                                                    < span className = "text-[7px] text-slate-400" > Tier - mix vs baseline </span>
                                                                                                                                                        </div>
                                                                                                                                                        < div className = "p-1.5 border border-slate-100 rounded text-center" >
                                                                                                                                                            <span className="text-[8px] font-bold block mb-1" > Live Charts </span>
                                                                                                                                                                < span className = "text-[7px] text-slate-400" > Aggregated Demand, Personas </span>
                                                                                                                                                                    </div>
                                                                                                                                                                    < div className = "p-1.5 border border-amber-200 bg-amber-50/50 rounded text-center flex flex-col items-center justify-center" >
                                                                                                                                                                        <FileDown className="w-3 h-3 text-amber-600 mb-1" />
                                                                                                                                                                            <span className="text-[8px] font-bold" > Generate Report </span>
                                                                                                                                                                                </div>
                                                                                                                                                                                </div>
                                                                                                                                                                                </div>
                                                                                                                                                                                </div>

                                                                                                                                                                                </div>
                                                                                                                                                                                </div>
                                                                                                                                                                                </div>
);

const VendorGuardArchitectureDiagram = () => (
    <div className= "w-full bg-[#111111] border border-slate-800 rounded-xl p-10 overflow-x-auto text-white" >
    <div className="min-w-[1000px] flex flex-col items-center" >

        {/* Top Row: Detection & Initial Storage */ }
        < div className = "flex items-center gap-8 mb-12" >
            <div className="flex flex-col items-center gap-2" >
                <div className="w-40 p-4 border border-teal-400/30 rounded-[2rem] bg-teal-900/20 flex flex-col items-center text-center relative" >
                    <Cpu className="w-5 h-5 text-teal-400 mb-2" />
                        <span className="text-[10px] font-bold" > AI Generates Vendor Risk Alert </span>
                            </div>
                            </div>
                            < ArrowRight className = "w-4 h-4 text-slate-600" />
                                <div className="w-40 p-4 border border-blue-400/30 rounded-lg bg-blue-900/20 flex flex-col items-center text-center" >
                                    <FileSpreadsheet className="w-5 h-5 text-blue-400 mb-2" />
                                        <span className="text-[10px] font-bold" > Alert Saved to Spreadsheet </span>
                                            </div>
                                            < ArrowRight className = "w-4 h-4 text-slate-600" />
                                                <div className="w-40 p-4 border border-blue-400/30 rounded-lg bg-blue-900/20 flex flex-col items-center text-center" >
                                                    <LayoutDashboard className="w-5 h-5 text-blue-400 mb-2" />
                                                        <span className="text-[10px] font-bold" > Alert Appears on Dashboard </span>
                                                            </div>
                                                            < ArrowRight className = "w-4 h-4 text-slate-600" />
                                                                <div className="w-40 p-4 border border-purple-400/30 rounded-lg bg-purple-900/20 flex flex-col items-center text-center" >
                                                                    <Search className="w-5 h-5 text-purple-400 mb-2" />
                                                                        <span className="text-[10px] font-bold" > Analyst Clicks Analyze </span>
                                                                            </div>
                                                                            < ArrowRight className = "w-4 h-4 text-slate-600" />
                                                                                <div className="w-40 p-4 border border-purple-400/30 rounded-lg bg-purple-900/20 flex flex-col items-center text-center" >
                                                                                    <Cpu className="w-5 h-5 text-purple-400 mb-2" />
                                                                                        <span className="text-[10px] font-bold" > LLM Returns Remediation Plan </span>
                                                                                            </div>
                                                                                            </div>

{/* Main Flow Downward */ }
<div className="w-full flex justify-center mb-12" >
    <div className="flex flex-col items-center" >
        <div className="h-10 w-px bg-slate-700" > </div>
            < div className = "w-[850px] h-px bg-slate-700" > </div>
                < div className = "h-10 w-px bg-slate-700 self-start ml-[75px]" > </div>
                    </div>
                    </div>

{/* Decision Point & Paths */ }
<div className="flex items-start gap-16 w-full max-w-5xl justify-center relative" >

    {/* Analyst Decision */ }
    < div className = "relative mt-12" >
        <div className="w-32 h-32 bg-[#4A3728] border border-[#634E3C] rotate-45 flex items-center justify-center shadow-xl" >
            <div className="-rotate-45 flex flex-col items-center text-center p-2" >
                <User className="w-6 h-6 text-orange-200 mb-1" />
                    <span className="text-[11px] font-bold text-orange-50 leading-tight" > Analyst Reviews Plan </span>
                        </div>
                        </div>
{/* Decision Labels */ }
<div className="absolute top-0 -right-12 text-[10px] font-bold text-slate-400" > Approve </div>
    < div className = "absolute bottom-0 -right-10 text-[10px] font-bold text-slate-400" > Reject </div>
        </div>

{/* The Paths */ }
<div className="flex flex-col gap-10" >

    {/* Approval Path Box */ }
    < div className = "p-6 border border-green-500/30 rounded-xl bg-green-950/10 flex flex-col gap-4 relative" >
        <div className="flex items-center gap-2 mb-2" >
            <CheckCircle className="w-3 h-3 text-green-400" />
                <span className="text-[10px] font-bold tracking-widest text-green-400 uppercase" > Approval Path </span>
                    </div>
                    < div className = "flex items-center gap-6" >
                        <div className="w-36 p-3 border border-green-400/20 rounded bg-green-900/20 flex flex-col items-center text-center" >
                            <ClipboardCheck className="w-4 h-4 text-green-400 mb-2" />
                                <span className="text-[9px] font-bold" > Create Jira Ticket </span>
                                    </div>
                                    < ArrowRight className = "w-3 h-3 text-slate-700" />
                                        <div className="w-36 p-3 border border-green-400/20 rounded bg-green-900/20 flex flex-col items-center text-center" >
                                            <FileSpreadsheet className="w-4 h-4 text-green-400 mb-2" />
                                                <span className="text-[9px] font-bold" > Update Excel </span>
                                                    </div>
                                                    < ArrowRight className = "w-3 h-3 text-slate-700" />
                                                        <div className="w-36 p-3 border border-green-400/20 rounded bg-green-900/20 flex flex-col items-center text-center" >
                                                            <Mail className="w-4 h-4 text-green-400 mb-2" />
                                                                <span className="text-[9px] font-bold" > Send Approval Email </span>
                                                                    </div>
                                                                    </div>
                                                                    </div>

{/* Rejection Path Box */ }
<div className="p-6 border border-red-500/30 rounded-xl bg-red-950/10 flex flex-col gap-4" >
    <div className="flex items-center gap-2 mb-2" >
        <XCircle className="w-3 h-3 text-red-400" />
            <span className="text-[10px] font-bold tracking-widest text-red-400 uppercase" > Rejection Path </span>
                </div>
                < div className = "flex items-center gap-6" >
                    <div className="w-36 p-3 border border-red-400/20 rounded bg-red-900/20 flex flex-col items-center text-center" >
                        <FileSpreadsheet className="w-4 h-4 text-red-400 mb-2" />
                            <span className="text-[9px] font-bold" > Log to Rejected Sheet </span>
                                </div>
                                < ArrowRight className = "w-3 h-3 text-slate-700" />
                                    <div className="w-36 p-3 border border-red-400/20 rounded bg-red-900/20 flex flex-col items-center text-center" >
                                        <Mail className="w-4 h-4 text-red-400 mb-2" />
                                            <span className="text-[9px] font-bold" > Send Rejection Email </span>
                                                </div>
                                                </div>
                                                </div>

                                                </div>
                                                </div>
                                                </div>
                                                </div>
);

const CRAArchitectureDiagram = () => (
    <div className= "w-full bg-[#fdfdfd] border border-slate-200 rounded-xl p-8 overflow-x-auto" >
    <div className="min-w-[900px] flex flex-col gap-10 relative" >

        {/* Top Layer: Users */ }
        < div className = "flex justify-around items-start" >
            <div className="flex flex-col items-center gap-2" >
                <div className="w-48 p-4 border border-slate-300 rounded-lg bg-white shadow-sm flex flex-col items-center text-center" >
                    <User className="w-6 h-6 text-slate-700 mb-2" />
                        <span className="text-[11px] font-bold text-slate-900 leading-tight" > Procurement / IT User Dashboard </span>
                            </div>
                            < div className = "flex flex-col items-center" >
                                <div className="h-8 w-px bg-slate-400 border-dashed border-l" > </div>
                                    < div className = "text-[8px] text-slate-500 font-bold uppercase italic mt-1" > Navigates pages, applies filters </div>
                                        < ArrowRight className = "w-3 h-3 text-slate-400 rotate-90" />
                                            </div>
                                            </div>

                                            < div className = "flex flex-col items-center gap-2" >
                                                <div className="w-48 p-4 border border-slate-300 rounded-lg bg-white shadow-sm flex flex-col items-center text-center" >
                                                    <Mail className="w-6 h-6 text-slate-700 mb-2" />
                                                        <div className="flex flex-col" >
                                                            <span className="text-[11px] font-bold text-slate-900 leading-tight" > Stakeholder </span>
                                                                < span className = "text-[9px] text-slate-500" > (Procurement Team / Approver)</span>
                                                                    < span className = "text-[9px] text-slate-500 italic mt-1" > Triggers via Email Button </span>
                                                                        </div>
                                                                        </div>
                                                                        < div className = "flex flex-col items-center" >
                                                                            <div className="h-8 w-px bg-slate-400 border-dashed border-l" > </div>
                                                                                < div className = "text-[8px] text-slate-500 font-bold uppercase italic mt-1" > Clicks action button in email </div>
                                                                                    < ArrowRight className = "w-3 h-3 text-slate-400 rotate-90" />
                                                                                        </div>
                                                                                        </div>
                                                                                        </div>

{/* Middle Layer: Core Services */ }
<div className="flex items-start gap-8 relative px-4" >

    {/* Dashboard Block */ }
    < div className = "flex-1 border-2 border-blue-100 rounded-xl p-4 bg-white shadow-sm" >
        <div className="flex items-center gap-2 mb-4 pb-2 border-b border-blue-50" >
            <LayoutDashboard className="w-4 h-4 text-blue-600" />
                <span className="text-xs font-bold text-blue-900" > Dashboard(User Interface) </span>
                    </div>
                    < div className = "space-y-3" >
                        <div className="p-2 bg-blue-50/50 border border-blue-100 rounded text-center" >
                            <div className="text-[9px] font-bold text-blue-800 uppercase mb-1" > Collapsible Left Panel(Filters) </div>
                                < div className = "text-[8px] text-slate-600" > Owner, Vendor, Criticality, License Type, Contract ID </div>
                                    </div>
                                    < div className = "grid grid-cols-3 gap-2" >
                                        <div className="p-2 border border-slate-100 rounded text-[8px] bg-slate-50" >
                                            <span className="font-bold block mb-1" > Actions </span>
KPIs, Util, Budget, Timeline
    </div>
    < div className = "p-2 border border-slate-100 rounded text-[8px] bg-slate-50" >
        <span className="font-bold block mb-1" > License </span>
                Deep Dive, True - Up
    </div>
    < div className = "p-2 border border-slate-100 rounded text-[8px] bg-slate-50" >
        <span className="font-bold block mb-1" > Budget </span>
                Budget vs Actual, Forecast
    </div>
    </div>
    </div>
    </div>

{/* Horizontal Connector */ }
<div className="flex items-center self-center h-10" >
    <ArrowRight className="w-5 h-5 text-slate-300" />
        </div>

{/* Backend Block */ }
<div className="flex-1 border-2 border-green-100 rounded-xl p-4 bg-white shadow-sm" >
    <div className="flex items-center gap-2 mb-4 pb-2 border-b border-green-50" >
        <Server className="w-4 h-4 text-green-600" />
            <span className="text-xs font-bold text-green-900" > Backend Service </span>
                </div>
                < div className = "space-y-2" >
                    <div className="p-2 border border-green-100 rounded bg-green-50/30" >
                        <span className="text-[9px] font-bold text-green-800 block" > Inbound Endpoint </span>
                            < span className = "text-[8px] text-green-600 font-medium" > (Webhooks / Events) </span>
                                </div>
                                < div className = "p-2 border border-green-100 rounded bg-green-50/30" >
                                    <span className="text-[9px] font-bold text-green-800 block" > Action Endpoint </span>
                                        < span className = "text-[8px] text-green-600 font-medium" > (Contract ID, Stage)</span>
                                            </div>
                                            < div className = "p-2 border border-green-100 rounded bg-green-50/30" >
                                                <span className="text-[9px] font-bold text-green-800 block" > Agent Orchestrator </span>
                                                    < span className = "text-[8px] text-green-600 font-medium" > (Coordinates Workflow)</span>
                                                        </div>
                                                        </div>
                                                        </div>

{/* Horizontal Connector */ }
<div className="flex items-center self-center h-10" >
    <ArrowRight className="w-5 h-5 text-slate-300" />
        </div>

{/* Agent Logic Block */ }
<div className="flex-[1.5] border-2 border-purple-100 rounded-xl p-4 bg-white shadow-sm relative" >
    <div className="flex items-center gap-2 mb-4 pb-2 border-b border-purple-50" >
        <Brain className="w-4 h-4 text-purple-600" />
            <span className="text-xs font-bold text-purple-900" > Agent Logic </span>
                </div>
                < div className = "flex flex-col gap-2" >
                {
                    [
                    { id: 1, title: 'Observe', desc: '(Process payload)' },
                    { id: 2, title: 'Plan', desc: '(Next step rules)' },
                    { id: 3, title: 'Send Relay Email', desc: '(Action buttons)', active: true },
                    { id: 4, title: 'Update Stage', desc: '(Persist state)', active: true },
                    { id: 5, title: 'Loop', desc: '(Continue workflow)' },
            ].map((step) => (
                        <div key= { step.id } className = {`p-1.5 border rounded flex items-center justify-between ${step.active ? 'bg-pink-50 border-pink-100' : 'bg-white border-slate-100'}`} >
                    <div className="flex flex-col" >
                        <span className="text-[9px] font-bold text-slate-900" > { step.id }. { step.title } </span>
                            < span className = "text-[8px] text-slate-500 leading-none" > { step.desc } </span>
                                </div>
{ step.active && <Zap className="w-3 h-3 text-pink-500" />}
</div>
            ))}
</div>

{/* Email Connector */ }
<div className="absolute top-[48%] -right-24 flex items-center" >
    <div className="w-12 h-px bg-slate-300 border-dashed border-t" > </div>
        < div className = "flex flex-col items-center ml-2" >
            <Mail className="w-4 h-4 text-amber-500" />
                <span className="text-[7px] font-bold text-slate-400 uppercase mt-1" > Email </span>
                    </div>
                    </div>
                    </div>
                    </div>

{/* Bottom Layer: Storage */ }
<div className="flex justify-start gap-16 px-12 pt-4" >
    <div className="flex flex-col items-center gap-2" >
        <ArrowRight className="w-4 h-4 text-slate-300 rotate-90" />
            <div className="p-4 border-2 border-green-200 rounded-full bg-green-50/50 w-24 h-24 flex flex-col items-center justify-center text-center" >
                <Database className="w-5 h-5 text-green-700 mb-1" />
                    <span className="text-[9px] font-bold text-green-900" > Data Repository </span>
                        </div>
                        </div>

                        < div className = "flex flex-col items-center gap-2" >
                            <ArrowRight className="w-4 h-4 text-slate-300 rotate-90" />
                                <div className="p-4 border-2 border-amber-200 rounded-xl bg-amber-50/50 w-24 h-24 flex flex-col items-center justify-center text-center" >
                                    <FileJson className="w-5 h-5 text-amber-700 mb-1" />
                                        <span className="text-[9px] font-bold text-amber-900" > Agent State Store </span>
                                            </div>
                                            </div>
                                            </div>
                                            </div>
                                            </div>
);

// --- REFINED NEGOTIATION ARCHITECTURE DIAGRAM ---

const NegotiationArchitectureDiagram = () => (
    <div className= "w-full bg-[#fdfdfd] border border-slate-200 rounded-xl p-8 overflow-x-auto" >
    <div className="min-w-[1000px] flex flex-col gap-6 relative" >

        {/* Title Header */ }
        < div className = "flex items-center gap-2 mb-4" >
            <div className="p-1 bg-[#10b981] rounded text-white" > <Layers className="w-4 h-4" /> </div>
                < h2 className = "text-sm font-bold text-slate-900 uppercase tracking-tight" > High - Level Architecture: Negotiation Ecosystem </h2>
                    </div>

{/* Main Grid: Rows & Columns based on image layout */ }
<div className="grid grid-cols-12 gap-2 relative" >

    {/* Column 1: Data Sources */ }
    < div className = "col-span-3 flex flex-col gap-6 pt-4" >
        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1" > 1. Data Sources </div>

            < div className = "p-4 border border-slate-100 rounded-xl bg-white shadow-sm flex flex-col gap-4 relative group" >
                {/* Box 1: User Input */ }
                < div className = "p-3 border border-slate-200 rounded-lg flex items-center gap-3 bg-white" >
                    <User className="w-5 h-5 text-blue-500" />
                        <div className="flex flex-col" >
                            <span className="text-[11px] font-bold text-slate-900" > User Input </span>
                                < span className = "text-[9px] text-slate-500" > (Negotiation Engine - Vendor Selection)</span>
                                    </div>
                                    </div>

{/* Box 2: Tavily Search */ }
<div className="p-3 border border-slate-200 rounded-lg flex items-center gap-3 bg-white" >
    <Search className="w-5 h-5 text-purple-500" />
        <div className="flex flex-col" >
            <span className="text-[11px] font-bold text-slate-900" > Tavily Search </span>
                < span className = "text-[9px] text-slate-500" > (Search Integration)</span>
                    </div>
                    </div>

{/* Outbound Arrow to Block 2 */ }
<div className="absolute top-1/2 -right-8 flex items-center translate-y-[-50%]" >
    <ArrowRight className="w-5 h-5 text-slate-300" />
        </div>
        </div>
        </div>

{/* Column 2: Ingestion & Processing */ }
<div className="col-span-4 flex flex-col gap-6 pt-4 pl-6" >
    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1" > 2. Ingestion & Processing </div>

        < div className = "p-4 border border-slate-100 rounded-xl bg-white shadow-sm flex flex-col gap-2 relative" >
            <div className="flex items-center gap-3 p-2.5 border-b border-slate-50" >
                <Cpu className="w-4 h-4 text-blue-600" />
                    <div className="flex flex-col" >
                        <span className="text-[11px] font-bold text-slate-900" > Data Fetching </span>
                            < span className = "text-[9px] text-slate-500" > (Python Backend)</span>
                                </div>
                                </div>
                                < div className = "flex items-center gap-3 p-2.5 border-b border-slate-50" >
                                    <Settings className="w-4 h-4 text-amber-500" />
                                        <span className="text-[11px] font-semibold text-slate-700" > API Response Handling </span>
                                            </div>
                                            < div className = "flex items-center gap-3 p-2.5 border-b border-slate-50" >
                                                <Database className="w-4 h-4 text-blue-400" />
                                                    <span className="text-[11px] font-semibold text-slate-700" > Data Structuring </span>
                                                        </div>
                                                        < div className = "flex items-center gap-3 p-2.5" >
                                                            <Server className="w-4 h-4 text-slate-400" />
                                                                <span className="text-[11px] font-semibold text-slate-700" > Content Aggregation </span>
                                                                    </div>

{/* Center Join Arrow */ }
<div className="absolute top-[40%] -right-12 flex items-center" >
    <svg width="40" height = "100" viewBox = "0 0 40 100" fill = "none" className = "text-slate-300" >
        <path d="M0 20 H20 V50 H40" stroke = "currentColor" strokeWidth = "1.5" />
            <path d="M0 80 H20 V50" stroke = "currentColor" strokeWidth = "1.5" />
                <path d="M40 50 L35 45 M40 50 L35 55" stroke = "currentColor" strokeWidth = "1.5" />
                    </svg>
                    </div>
                    </div>
                    </div>

{/* Column 3: Storage Layer */ }
<div className="col-span-4 flex flex-col gap-6 pt-4 pl-12" >
    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1" > 3. Storage / Caching Layer </div>
        < div className = "p-6 border border-slate-100 rounded-xl bg-white shadow-sm flex items-center justify-center h-48" >
            <div className="p-4 border border-slate-200 rounded-lg flex items-center gap-4 bg-white w-full" >
                <div className="w-10 h-10 rounded bg-amber-50 flex items-center justify-center" >
                    <Database className="w-5 h-5 text-amber-600" />
                        </div>
                        < div className = "flex flex-col" >
                            <span className="text-[12px] font-bold text-slate-900" > Temporary Data Cache </span>
                                < span className = "text-[10px] text-slate-500" > (Vendor Data)</span>
                                    </div>
                                    </div>
                                    </div>
                                    </div>

                                    </div>

{/* Row 2: Flow down from Storage to Engines */ }
<div className="flex items-center justify-center relative py-2" >
    {/* Complex routing arrow from image (3rd block down to 5th/4th) */ }
    < svg width = "100%" height = "80" viewBox = "0 0 1000 80" fill = "none" className = "absolute -top-10 left-0 pointer-events-none" >
        {/* Path from Block 2 and 3 down to Engines and Viz */ }
        < path d = "M500 0 V40 H700 V80" stroke = "#e2e8f0" strokeWidth = "2" />
            <path d="M700 80 L695 75 M700 80 L705 75" stroke = "#e2e8f0" strokeWidth = "2" />
                </svg>
                </div>

                < div className = "grid grid-cols-12 gap-8 mt-4" >

                    {/* Column 4: Engines & Generation */ }
                    < div className = "col-span-4 flex flex-col gap-6" >
                        <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1" > 4. Engines & Generation </div>
                            < div className = "p-4 border border-slate-100 rounded-xl bg-white shadow-sm flex flex-col gap-3 relative" >
                                <div className="flex items-center gap-3 p-2 bg-slate-50/50 rounded-lg" >
                                    <Cpu className="w-4 h-4 text-blue-600" />
                                        <span className="text-[11px] font-bold text-slate-700" > Python Backend Logic </span>
                                            </div>
                                            < div className = "flex items-center gap-3 p-2 bg-slate-50/50 rounded-lg" >
                                                <FileText className="w-4 h-4 text-teal-600" />
                                                    <span className="text-[11px] font-bold text-slate-700" > Briefing Doc Generator </span>
                                                        </div>
                                                        < div className = "flex items-center gap-3 p-2 bg-slate-50/50 rounded-lg" >
                                                            <MessageSquare className="w-4 h-4 text-purple-600" />
                                                                <div className="flex flex-col" >
                                                                    <span className="text-[11px] font-bold text-slate-900" > AI Chatbot Engine </span>
                                                                        < span className = "text-[9px] text-slate-500" > (OpenAI Integration)</span>
                                                                            </div>
                                                                            </div>

{/* Arrow right to Visualization */ }
<div className="absolute top-1/2 -right-10 flex items-center" >
    <ArrowRight className="w-6 h-6 text-slate-300" />
        </div>
        </div>
        </div>

{/* Column 5: Visualization & Consumption */ }
<div className="col-span-6 flex flex-col gap-6 pl-10" >
    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1" > 5. Visualization & Consumption </div>
        < div className = "p-5 border-2 border-blue-50 rounded-2xl bg-white shadow-md flex flex-col gap-3" >
            <div className="flex items-center gap-3 mb-2 border-b border-slate-50 pb-3" >
                <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center" >
                    <LayoutDashboard className="w-4 h-4 text-blue-600" />
                        </div>
                        < span className = "text-[13px] font-bold text-slate-900" > React Frontend </span>
                            </div>

{/* The Tab Stack from image */ }
<div className="space-y-1.5" >
    <div className="p-3 bg-blue-50/30 border border-blue-100 rounded-lg flex flex-col gap-0.5" >
        <span className="text-[11px] font-bold text-blue-900" > Highlights Tab </span>
            < span className = "text-[9px] text-blue-600 italic" > (Price, Product, AI / Cloud, Topics) </span>
                </div>
                < div className = "p-2.5 bg-slate-50 border border-slate-100 rounded-lg text-center" >
                    <span className="text-[11px] font-semibold text-slate-700" > Earnings Summary Tab </span>
                        </div>
                        < div className = "p-2.5 bg-slate-50 border border-slate-100 rounded-lg text-center" >
                            <span className="text-[11px] font-semibold text-slate-700" > QBR Tab </span>
                                </div>
                                < div className = "p-2.5 bg-slate-50 border border-slate-100 rounded-lg text-center" >
                                    <span className="text-[11px] font-semibold text-slate-700" > Briefing Docs Tab </span>
                                        </div>
                                        </div>
                                        </div>
                                        </div>

                                        </div>

{/* Background visual elements to replicate the floating chevrons in image */ }
<div className="absolute top-[35%] left-[26%] opacity-20" > <ChevronRightSquare className="w-6 h-6 text-slate-400" /> </div>
    < div className = "absolute top-[35%] left-[68%] opacity-20" > <ChevronRightSquare className="w-6 h-6 text-slate-400" /> </div>
        < div className = "absolute top-[80%] left-[48%] opacity-20" > <ChevronRightSquare className="w-6 h-6 text-slate-400" /> </div>
            </div>
            </div>
);

// --- Section Views ---

const SummaryView = ({ module }) => {
    const isCra = module === 'cra';
    const isDpe = module === 'dpe';
    const isVg = module === 'vendorGuard';

    let config;
    if (isDpe) {
        config = {
            title: "Spend Intelligence",
            subtitle: "Strategic Spend Analysis & Forecasting",
            outcome: "Data-driven clarity for the first and most critical stage of strategic sourcing.",
            problems: [
                "Over-provisioning of licenses and unplanned renewals.",
                "Suboptimal vendor agreements due to unclear software demand.",
                "Relying on estimation for net-new vendor procurement without historical data."
            ],
            solutions: [
                "Forecasts license requirements and establishes a structured demand baseline.",
                "Case 2 Workspace performs semantic matching for net-new vendors.",
                "Live market benchmarking and negotiation delta calculations."
            ]
        };
    } else if (isCra) {
        config = {
            title: "Contract Execution",
            subtitle: "Software Asset Forecast Engine & Renewal Assistant",
            outcome: "Optimizing software spend through high-fidelity spend forecasting and autonomous license harvesting agents.",
            problems: [
                "Fragmented, reactive, and error-prone enterprise contract renewals",
                "Overpayment for underutilized licenses and surprise true-up costs",
                "Endless email ping-pong without a consistent audit trail"
            ],
            solutions: [
                "Automated 5-stage workflow (Planning to Closed)",
                "Role-based AI relay emails with single-click action buttons",
                "Deterministic state tracking and real-time portfolio dashboards"
            ]
        };
    } else if (isVg) {
        config = {
            title: "Risk Governance",
            subtitle: "Vendor Risk Intelligence & Remediation",
            outcome: "Faster, safer, and automated vendor risk decision-making through an AI-driven vendor risk intelligence and remediation system.",
            problems: [
                "Vendor risks are spread across security alerts, compliance notices, breach reports, and feeds.",
                "Manual vendor risk analysis is slow, inconsistent, and difficult to scale.",
                "Existing vendor reviews lack real-time alert generation and automated remediation.",
                "Lack of traceable approval workflows and unified dashboard visibility."
            ],
            solutions: [
                "Intelligence Layer: Aggregates vendor data from structured and unstructured sources.",
                "Real-time Alerts: Automatically generates vendor-specific risk alerts.",
                "AI Analysis: Uses LLM intelligence to classify severity and generate remediation strategies.",
                "Remediation: Automates approval workflows, Jira ticket creation, and email notifications."
            ]
        };
    } else {
        config = {
            title: "Vendor Intelligence",
            subtitle: "Strategic Intelligence & Decision Support",
            outcome: "Faster, safer, and data-driven vendor decisions through an AI-driven unified intelligence layer.",
            problems: [
                "Vendor intelligence is fragmented across earnings calls, filings, and risk feeds.",
                "Manual analysis is slow, inconsistent, and lacks traceability.",
                "High effort required to extract commercial signals for QBRs."
            ],
            solutions: [
                "Aggregates signals across structured and unstructured data sources.",
                "Converts raw data into evidence-backed executive insights.",
                "Automates reporting for strategic vendor relationship management."
            ]
        };
    }

    return (
        <div className= "space-y-8" >
        <Card className="p-8 border-l-[6px] border-l-[#0B1F3A]" >
            <div className="max-w-4xl" >
                <div className="flex items-center gap-2 mb-3" >
                    <div className="h-px w-8 bg-slate-300" />
                        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-[0.2em]" > Module Synopsis </span>
                            </div>
                            < h1 className = "text-3xl font-bold text-[#0B1F3A] mb-2 tracking-tight" > { config.title } </h1>
                                < p className = "text-lg text-slate-600 mb-8 font-medium italic" > { config.subtitle } </p>

                                    < div className = "flex items-start gap-4 p-5 bg-slate-50 rounded-lg border border-slate-200" >
                                        <Rocket className="w-5 h-5 text-teal-600 shrink-0 mt-1" />
                                            <div>
                                            <h3 className="font-bold text-slate-900 text-sm mb-1 uppercase tracking-wider" > Strategic Objective </h3>
                                                < p className = "text-slate-800 leading-relaxed font-medium" > { config.outcome } </p>
                                                    </div>
                                                    </div>
                                                    </div>
                                                    </Card>

                                                    < div className = "grid grid-cols-12 gap-8" >
                                                        <Card className="col-span-12 md:col-span-6 p-8" >
                                                            <div className="flex items-center justify-between mb-6 border-b border-slate-100 pb-4" >
                                                                <h3 className="text-lg font-bold text-[#0B1F3A] flex items-center gap-3" >
                                                                    <ShieldAlert className="w-5 h-5 text-slate-500" /> Critical Gaps
                                                                        </h3>
                                                                        </div>
                                                                        < ul className = "space-y-5" >
                                                                        {
                                                                            config.problems.map((p, i) => (
                                                                                <li key= { i } className = "flex gap-4 items-start" >
                                                                                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 mt-2.5 shrink-0" />
                                                                            <span className="text-sm text-slate-800 leading-relaxed font-semibold" > { p } </span>
                                                                            </li>
                                                                            ))
                                                                        }
                                                                            </ul>
                                                                            </Card>

                                                                            < Card className = "col-span-12 md:col-span-6 p-8" >
                                                                                <div className="flex items-center justify-between mb-6 border-b border-slate-100 pb-4" >
                                                                                    <h3 className="text-lg font-bold text-[#0B1F3A] flex items-center gap-3" >
                                                                                        <Lightbulb className="w-5 h-5 text-teal-500" /> Proposed Capability
                                                                                            </h3>
                                                                                            </div>
                                                                                            < ul className = "space-y-5" >
                                                                                            {
                                                                                                config.solutions.map((s, i) => (
                                                                                                    <li key= { i } className = "flex gap-4 items-start" >
                                                                                                    <CheckCircle2 className="w-5 h-5 shrink-0 text-teal-500 mt-0.5" />
                                                                                                <span className="text-sm text-slate-800 leading-relaxed font-semibold" > { s } </span>
                                                                                                </li>
                                                                                                ))
                                                                                            }
                                                                                                </ul>
                                                                                                </Card>
                                                                                                </div>
                                                                                                </div>
  );
};

const AchievedView = ({ module }) => {
    const isCra = module === 'cra';
    const isDpe = module === 'dpe';
    const isVg = module === 'vendorGuard';
    let data, months, defaultMonth;
    if (isDpe) {
        data = DPE_TIMELINE_DATA;
        months = [{ id: 'February 2026', label: 'FEB 2026' }, { id: 'March 2026', label: 'MAR 2026' }, { id: 'April 2026', label: 'APR 2026' }, { id: 'May 2026', label: 'MAY 2026' }];
        defaultMonth = 'April 2026';
    } else if (isCra) {
        data = CRA_TIMELINE_DATA;
        months = [{ id: 'January 2026', label: 'JAN 2026' }, { id: 'February 2026', label: 'FEB 2026' }, { id: 'March 2026', label: 'MAR 2026' }, { id: 'April 2026', label: 'APR 2026' }];
        defaultMonth = 'March 2026';
    } else if (isVg) {
        data = VENDOR_GUARD_TIMELINE_DATA;
        months = [{ id: 'February 2026', label: 'FEB 2026' }, { id: 'March 2026', label: 'MAR 2026' }, { id: 'April 2026', label: 'APR 2026' }, { id: 'May 2026', label: 'MAY 2026' }, { id: 'Enterprise Enhancements', label: 'ENTERPRISE' }];
        defaultMonth = 'April 2026';
    } else {
        data = NEGOTIATION_TIMELINE_DATA;
        months = [{ id: 'February 2026', label: 'FEB 2026' }, { id: 'March 2026', label: 'MAR 2026' }, { id: 'April 2026', label: 'APR 2026' }, { id: 'May 2026', label: 'MAY 2026' }];
        defaultMonth = 'April 2026';
    }
    const [selectedMonth, setSelectedMonth] = useState(defaultMonth);
    return (
        <div className= "space-y-8" >
        <Card className="py-10 px-8" >
            <div className="relative flex justify-between items-center w-full max-w-5xl mx-auto" >
                <div className="absolute top-1/2 left-0 w-full h-[2px] bg-slate-200 -translate-y-1/2 z-0" />
                {
                    months.map((m) => {
                        const isSelected = selectedMonth === m.id;
                        return (
                            <div key= { m.id } className = "relative z-10 flex flex-col items-center cursor-pointer" onClick = {() => setSelectedMonth(m.id)}>
                                <div className={ `w-3.5 h-3.5 rounded-full border-2 transition-all ${isSelected ? 'bg-white border-[#0B1F3A] ring-4 ring-slate-100 scale-125' : 'bg-slate-300 border-transparent hover:bg-slate-500'}` } />
                                    < span className = {`text-[10px] font-bold tracking-[0.15em] whitespace-nowrap px-4 py-2 mt-4 rounded-full transition-all ${isSelected ? 'text-[#0B1F3A] bg-slate-100' : 'text-slate-500'}`}> { m.label } </span>
                                        </div>
            );
          })}
</div>
    </Card>
    < div >
    <div className="flex items-center gap-3 mb-6" >
        <h3 className="text-xl font-bold text-[#0B1F3A]" > { selectedMonth } Deliverables </h3>
            < div className = "h-px flex-1 bg-slate-200" />
                </div>
                < div className = "grid grid-cols-12 gap-6" >
                {
                    data[selectedMonth]?.map((item, i) => (
                        <Card key= { i } className = "col-span-12 lg:col-span-4 p-6 flex flex-col min-h-[140px]" >
                        <div className="flex-1" >
                    <div className="flex items-center justify-between mb-3" >
                    <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest" > { item.category } </span>
                    < StatusBadge status = { item.status } />
                    </div>
                    < p className = "text-sm font-bold text-slate-900 leading-snug" > { item.task } </p>
                    </div>
                    < div className = "flex justify-end pt-4" >
                    <ChevronRight className="w-4 h-4 text-slate-400" />
                    </div>
                    </Card>
                    ))
                }
                    </div>
                    </div>
                    </div>
  );
};

const PhasesView = ({ module }) => {
    const isCra = module === 'cra';
    const isDpe = module === 'dpe';
    const isVg = module === 'vendorGuard';
    const phase1 = isDpe ? DPE_PHASE_1_DETAILS : (isCra ? CRA_PHASE_1_DETAILS : (isVg ? VG_PHASE_1_DETAILS : NEGOTIATION_PHASE_1_DETAILS));
    const phase2 = isDpe ? DPE_PHASE_2_DETAILS : (isCra ? CRA_PHASE_2_DETAILS : (isVg ? VG_PHASE_2_DETAILS : null));
    const PhaseTable = ({ title, status, data, statusColor }) => (
        <Card className= "mb-10 overflow-hidden" >
        <div className="px-8 py-5 border-b border-slate-200 bg-slate-50 flex justify-between items-center" >
            <h3 className="text-lg font-bold text-[#0B1F3A] tracking-tight" > { title } </h3>
                < span className = {`px-2.5 py-1 text-[10px] font-bold tracking-widest rounded border ${statusColor}`
}> { status } </span>
    </div>
    < div className = "grid grid-cols-12 bg-white px-8 py-3 text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] border-b border-slate-100" >
        <div className="col-span-12 md:col-span-4" > Strategic Initiative </div>
            < div className = "col-span-12 md:col-span-8" > Business Impact & Capability </div>
                </div>
                < div className = "divide-y divide-slate-100" >
                {
                    data.map((item, i) => (
                        <div key= { i } className = "grid grid-cols-12 px-8 py-6 hover:bg-slate-50 transition-colors" >
                        <div className="col-span-12 md:col-span-4 pr-6" >
                    <div className="flex items-start gap-3" >
                    <div className="w-1.5 h-1.5 rounded-full bg-teal-600 mt-2 shrink-0" />
                    <p className="text-sm font-bold text-slate-900 leading-tight" > { item.tech } </p>
                    </div>
                    </div>
                    < div className = "col-span-12 md:col-span-8 mt-2 md:mt-0" >
                    <p className="text-sm text-slate-700 leading-relaxed font-semibold" > { item.impact } </p>
                    </div>
                    </div>
                    ))
                }
                    </div>
                    </Card>
  );
return (
    <div className= "space-y-2" >
    <div className="mb-10 flex flex-col gap-1" >
        <h2 className="text-2xl font-bold text-[#0B1F3A] tracking-tight" > Deployment Roadmap </h2>
            < div className = "h-1 w-12 bg-teal-500 rounded-full" />
                </div>
                < PhaseTable title = "PHASE I: FOUNDATION & INTELLIGENCE" status = "ACHIEVED" data = { phase1 } statusColor = "bg-teal-50 text-teal-700 border-teal-200" />
                    { phase2 && <PhaseTable title="PHASE II: ADVANCED AGENTIC SCALING" status = "ACTIVE" data = { phase2 } statusColor = "bg-blue-50 text-blue-700 border-blue-200" />}
</div>
  );
};

const TechStackView = ({ module }) => {
    const isCra = module === 'cra';
    const isDpe = module === 'dpe';
    const isVg = module === 'vendorGuard';
    const isNeg = module === 'negotiationEngine';

    return (
        <div className= "space-y-12" >
        {/* System Architecture Section */ }
        < div >
        <div className="flex items-center gap-3 mb-6" >
            <h3 className="text-xl font-bold text-[#0B1F3A]" > System Architecture </h3>
                < div className = "h-px flex-1 bg-slate-200" />
                    </div>

    {
        isDpe && (
            <div className="space-y-6" >
                <h4 className="text-sm font-bold text-slate-500 uppercase tracking-widest px-1" > Demand Engine Architecture / Agent Flow </h4>
                    < DemandEngineArchitectureDiagram />
                    </div>
        )}
{ isCra && <CRAArchitectureDiagram /> }
{ isNeg && <NegotiationArchitectureDiagram /> }
{
    isVg && (
        <div className="space-y-6" >
            <h4 className="text-sm font-bold text-slate-500 uppercase tracking-widest px-1" > Risk Governance Architecture </h4>
                < VendorGuardArchitectureDiagram />
                </div>
        )
}
</div>
    </div>
  );
};

const LandingPage = ({ onSelectApp }) => {
    const apps = [
        { id: 'dpe', title: 'Spend Intelligence', fullName: 'Strategic Spend Analysis & Forecasting', icon: <PieChart className="w-5 h-5" />, description: 'Consulting-grade clarity for establishing demand baselines and semantic matching for global procurement.' },
        { id: 'negotiationEngine', title: 'Vendor Intelligence', fullName: 'Strategic Intelligence & Support', icon: <Brain className="w-5 h-5" />, description: 'Unified framework for structured vendor insights, earnings analysis, and executive decision support.' },
        { id: 'vendorGuard', title: 'Risk Governance', fullName: 'Risk Intelligence & Remediation', icon: <ShieldCheck className="w-5 h-5" />, description: 'Autonomous risk surveillance aggregating security alerts, compliance drift, and breach data.' },
        { id: 'cra', title: 'Contract Execution', fullName: 'Automated Renewal Management (CRA)', icon: <TrendingUp className="w-5 h-5" />, description: 'Predictive spend forecasting and autonomous licensing intelligence for enterprise software assets.' }
    ];
    return (
        <div className= "p-10 max-w-7xl mx-auto w-full" >
        <div className="mb-14 max-w-3xl" >
            <div className="flex items-center gap-2 mb-4" > <div className="h-px w-10 bg-[#0B1F3A]" /> <span className="text-[11px] font-bold text-[#0B1F3A] uppercase tracking-[0.3em]" > Institutional Ecosystem < /span></div >
                <h1 className="text-4xl font-bold text-[#0B1F3A] mb-4 tracking-tight leading-tight" > Strategic Sourcing < br /> <span className="text-slate-500 font-light italic" > Command Center < /span></h1 >
                    <p className="text-lg text-slate-700 font-semibold leading-relaxed" > The Agivant ecosystem converts fragmented market signals into defensible vendor intelligence and automated operational efficiency.</p>
                        </div>
                        < div className = "grid grid-cols-12 gap-8" >
                        {
                            apps.map((app) => (
                                <button key= { app.id } onClick = {() => onSelectApp(app.id)} className = "col-span-12 md:col-span-6 lg:col-span-3 text-left group" >
                                    <Card className="h-full flex flex-col p-8 hover:border-[#0B1F3A] transition-colors border-slate-200" >
                                        <div className="w-12 h-12 bg-slate-100 text-[#0B1F3A] rounded-xl flex items-center justify-center mb-6 group-hover:bg-[#0B1F3A] group-hover:text-white transition-all" > { app.icon } </div>
                                            < div className = "flex-1" >
                                                <h3 className="text-lg font-bold text-[#0B1F3A] mb-1 group-hover:text-teal-600 transition-colors" > { app.title } </h3>
                                                    < p className = "text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4" > { app.fullName } </p>
                                                        < p className = "text-sm text-slate-800 font-semibold leading-relaxed mb-8" > { app.description } </p>
                                                            </div>
                                                            < div className = "mt-auto flex items-center justify-between border-t border-slate-100 pt-6" >
                                                                <span className="text-[10px] font-bold text-teal-700 tracking-widest uppercase" > Launch Application </span>
                                                                    < ArrowRight className = "w-4 h-4 text-slate-400 group-hover:text-[#0B1F3A] group-hover:translate-x-1 transition-all" />
                                                                        </div>
                                                                        </Card>
                                                                        </button>
        ))}
</div>
    </div>
  );
};

const App = () => {
    const [currentModule, setCurrentModule] = useState('home');
    const [activeTab, setActiveTab] = useState('summary');

    const handleModuleSwitch = (mod) => {
        setCurrentModule(mod);
        setActiveTab('summary');
    };

    const tabs = [
        { id: 'summary', label: 'STRATEGY', icon: <Info className="w-3.5 h-3.5 mr-2"/> },
        { id: 'achieved', label: 'MILESTONES', icon: <Calendar className="w-3.5 h-3.5 mr-2"/> },
        { id: 'phases', label: 'EVOLUTION', icon: <History className="w-3.5 h-3.5 mr-2"/> },
        { id: 'tech', label: 'ARCHITECTURE', icon: <Terminal className="w-3.5 h-3.5 mr-2"/> }
    ];

    return (
        <div className= "flex h-screen bg-[#F8FAFC] font-sans text-slate-900 overflow-hidden" >
        <aside className="w-72 bg-white border-r border-slate-200 flex flex-col z-20 shrink-0" >
            <div className="h-20 flex items-center px-8 border-b border-slate-100 cursor-pointer" onClick = {() => handleModuleSwitch('home')}>
                <div className="flex items-center gap-3" >
                    <img src="/agivant_logo_symbol.png" alt="Agivant Logo" className="w-8 h-8 object-contain" />
                        < div className = "flex flex-col" > <span className="font-bold text-[#0B1F3A] tracking-widest text-xs" > AGIVANT < /span><span className="text-[9px] text-teal-600 font-bold uppercase tracking-widest -mt-1">INTELLIGENCE</span > </div>
                            </div>
                            </div>
                            < nav className = "flex-1 overflow-y-auto py-8" >
                                <button onClick={ () => handleModuleSwitch('home') } className = {`w-full flex items-center px-8 py-3 text-[11px] font-bold uppercase tracking-[0.2em] ${currentModule === 'home' ? 'text-[#0B1F3A] border-r-4 border-teal-500 bg-slate-50' : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'}`}> <Grid className="w-4 h-4 mr-4 opacity-50" /> Command Center </button>
                                    < div className = "mt-10 mb-4 px-8 text-[9px] font-black text-slate-400 uppercase tracking-[0.3em]" > Strategic Assets </div>
                                        < button onClick = {() => handleModuleSwitch('dpe')} className = {`w-full flex items-center px-8 py-3.5 text-[11px] font-bold uppercase tracking-[0.15em] ${currentModule === 'dpe' ? 'text-[#0B1F3A] border-r-4 border-teal-500 bg-slate-50' : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'}`}> <div className={ `w-1.5 h-1.5 rounded-full mr-4 ${currentModule === 'dpe' ? 'bg-teal-500' : 'bg-slate-300'}` } />Spend Intelligence</button >
                                            <button onClick={ () => handleModuleSwitch('negotiationEngine') } className = {`w-full flex items-center px-8 py-3.5 text-[11px] font-bold uppercase tracking-[0.15em] ${currentModule === 'negotiationEngine' ? 'text-[#0B1F3A] border-r-4 border-teal-500 bg-slate-50' : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'}`}> <div className={ `w-1.5 h-1.5 rounded-full mr-4 ${currentModule === 'negotiationEngine' ? 'bg-teal-500' : 'bg-slate-300'}` } />Vendor Intelligence</button >
                                                <button onClick={ () => handleModuleSwitch('vendorGuard') } className = {`w-full flex items-center px-8 py-3.5 text-[11px] font-bold uppercase tracking-[0.15em] ${currentModule === 'vendorGuard' ? 'text-[#0B1F3A] border-r-4 border-teal-500 bg-slate-50' : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'}`}> <div className={ `w-1.5 h-1.5 rounded-full mr-4 ${currentModule === 'vendorGuard' ? 'bg-teal-500' : 'bg-slate-300'}` } />Risk Governance</button >
                                                    <button onClick={ () => handleModuleSwitch('cra') } className = {`w-full flex items-center px-8 py-3.5 text-[11px] font-bold uppercase tracking-[0.15em] ${currentModule === 'cra' ? 'text-[#0B1F3A] border-r-4 border-teal-500 bg-slate-50' : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'}`}> <div className={ `w-1.5 h-1.5 rounded-full mr-4 ${currentModule === 'cra' ? 'bg-teal-500' : 'bg-slate-300'}` } />Contract Execution</button >
                                                        </nav>
                                                            </aside>
                                                            < div className = "flex-1 flex flex-col min-w-0" >
                                                                <header className="h-20 bg-white border-b border-slate-200 flex items-center justify-between px-10 shrink-0 z-10" >
                                                                    <h2 className="text-sm font-bold text-[#0B1F3A] tracking-widest uppercase" > { currentModule === 'home' ? 'Strategic Sourcing Command Center' : `Active Module / ${currentModule === 'dpe' ? 'Spend Intelligence' : (currentModule === 'negotiationEngine' ? 'Vendor Intelligence' : (currentModule === 'vendorGuard' ? 'Risk Governance' : 'Contract Execution'))}`}</h2>
                                                                        < div className = "flex items-center gap-6" > <Bell className="w-4 h-4 text-slate-500 cursor-pointer hover:text-teal-600" /> <div className="h-4 w-px bg-slate-200" /> <Settings className="w-4 h-4 text-slate-500 cursor-pointer hover:text-teal-600" /> </div>
                                                                            </header>
{
    currentModule === 'home' ? (<main className= "flex-1 overflow-auto bg-[#F4F7F9]" > <LandingPage onSelectApp={ handleModuleSwitch } /></main >) : (
        <div className= "flex flex-col flex-1 min-h-0" >
        <div className="bg-white border-b border-slate-200 px-10 shrink-0" > <div className="flex space-x-10" >
        {
            tabs.map(tab => (
                <button key= { tab.id } onClick = {() => setActiveTab(tab.id)} className = {`flex items-center pt-6 pb-5 text-[10px] font-bold tracking-[0.2em] border-b-2 transition-all ${activeTab === tab.id ? 'border-[#0B1F3A] text-[#0B1F3A]' : 'border-transparent text-slate-500 hover:text-slate-800'}`
}>
    { tab.icon }{ tab.label }
</button>
              ))}
</div></div >
    <main className="flex-1 overflow-auto bg-[#F8FAFC]" > <div className="max-w-7xl mx-auto w-full p-10 pb-20" >
        { activeTab === 'summary' && <SummaryView module={ currentModule } />}
{ activeTab === 'achieved' && <AchievedView module={ currentModule } /> }
{ activeTab === 'phases' && <PhasesView module={ currentModule } /> }
{ activeTab === 'tech' && <TechStackView module={ currentModule } /> }
</div></main >
    </div>
        )}
</div>
    </div>
  );
};

export default App;