/**
 * OnboardingWizard — Validation Gate Pattern
 *
 * Every step: fetch data -> display on dedicated page -> await Continue or Cancel.
 * No step auto-advances. Every action is logged to the backend audit trail.
 *
 * Audit events emitted:
 *   WORKFLOW_STARTED  — wizard mounts and creates session
 *   DATA_FETCHED      — backend returns step data (emitted by backend too)
 *   USER_CONTINUED    — user clicked Continue
 *   USER_CANCELLED    — user clicked Cancel
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Search, ShieldCheck, AlertTriangle, FileText, Scale,
  CheckCircle2, XCircle, ChevronRight, Award, Zap,
  Building2, Users, DollarSign, Globe, Loader2,
  CheckSquare, Ban, RotateCcw, Clock, Package, Globe2,
} from 'lucide-react';

const API = 'http://localhost:8090';

// ── Step definitions ──────────────────────────────────────────────────────────

const STEPS = [
  {
    key:         'discovery',
    label:       'Supplier Discovery',
    agent:       'Discovery Agent',
    description: 'AI scan of market benchmarks and vendor profiles',
    icon:        Search,
    color:       '#3b82f6',
    bg:          '#eff6ff',
  },
  {
    key:         'qualification',
    label:       'Qualification Review',
    agent:       'Compliance Agent',
    description: 'SOC2, ISO 27001, GDPR and ESG verification',
    icon:        ShieldCheck,
    color:       '#8b5cf6',
    bg:          '#f5f3ff',
  },
  {
    key:         'risk',
    label:       'Risk Audit',
    agent:       'Risk Agent',
    description: 'Financial stability and cybersecurity assessment',
    icon:        AlertTriangle,
    color:       '#f59e0b',
    bg:          '#fffbeb',
  },
  {
    key:         'contract',
    label:       'Contract Review',
    agent:       'Contract Agent',
    description: 'MSA analysis and negotiation blueprint',
    icon:        FileText,
    color:       '#10b981',
    bg:          '#f0fdf4',
  },
  {
    key:         'decision',
    label:       'Decision Terminal',
    agent:       'Orchestrator',
    description: 'Aggregated system verdict and final approval',
    icon:        Scale,
    color:       '#6366f1',
    bg:          '#eef2ff',
  },
];

// ── Audit logger ──────────────────────────────────────────────────────────────

async function emitLog(sessionId, eventType, step, extra = {}) {
  try {
    await fetch(`${API}/sessions/${sessionId}/log`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_type: eventType, step, extra }),
    });
  } catch (_) {}
}

// ── Step data renderers ───────────────────────────────────────────────────────

function Card({ label, value, icon: Icon, accent }) {
  return (
    <div className="bg-white border border-slate-100 rounded-xl p-4 flex items-start space-x-3">
      {Icon && <Icon size={16} className="mt-0.5 flex-shrink-0" style={{ color: accent }} />}
      <div className="min-w-0">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-0.5">{label}</p>
        <p className="text-sm font-bold text-slate-800 truncate">{value || '—'}</p>
      </div>
    </div>
  );
}

function Tag({ children, color = '#3b82f6' }) {
  return (
    <span className="text-xs font-bold px-3 py-1 rounded-full"
      style={{ background: color + '18', color }}>
      {children}
    </span>
  );
}

function DiscoveryData({ data }) {
  return (
    <div className="space-y-5">
      {/* Company overview banner */}
      <div className="bg-blue-50 border border-blue-100 rounded-2xl p-6">
        <p className="text-[10px] font-black text-blue-400 uppercase tracking-widest mb-2">Company Overview</p>
        <p className="text-sm text-slate-700 leading-relaxed">{data.company_summary}</p>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Founded',        value: data.founded,         icon: Building2  },
          { label: 'Employees',      value: data.employees,       icon: Users      },
          { label: 'Revenue (est.)', value: data.revenue_estimate,icon: DollarSign },
          { label: 'Analyst Rating', value: data.analyst_rating,  icon: Award      },
        ].map(({ label, value, icon: Icon }) => (
          <div key={label} className="bg-white border border-slate-100 rounded-xl p-3 text-center">
            <Icon size={14} className="text-blue-400 mx-auto mb-1" />
            <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{label}</p>
            <p className="text-xs font-black text-slate-800 mt-0.5 leading-tight">{value || '—'}</p>
          </div>
        ))}
      </div>

      {/* HQ + Growth */}
      <div className="grid grid-cols-2 gap-3">
        <Card label="Headquarters" value={data.headquarters}  icon={Globe}         accent="#3b82f6" />
        <Card label="Growth Rate"  value={data.growth_rate}   icon={ChevronRight}  accent="#3b82f6" />
        <Card label="Funding"      value={data.recent_funding} icon={DollarSign}   accent="#3b82f6" />
        <Card label="Business Model" value={data.business_model} icon={Package}   accent="#3b82f6" />
      </div>

      {/* Products & descriptions */}
      {data.products?.length > 0 && (
        <div className="bg-white border border-slate-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Products & Services</p>
          <div className="space-y-2">
            {data.products.map((p, i) => (
              <div key={i} className="flex items-start space-x-3 py-2 border-b border-slate-50 last:border-0">
                <span className="w-2 h-2 rounded-full bg-blue-400 mt-1.5 flex-shrink-0" />
                <div>
                  <p className="text-sm font-bold text-slate-800">{p}</p>
                  {data.product_descriptions?.[p] && (
                    <p className="text-xs text-slate-500 mt-0.5">{data.product_descriptions[p]}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Technology stack */}
      {data.tech_stack?.length > 0 && (
        <div className="bg-white border border-slate-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Technology Stack</p>
          <div className="flex flex-wrap gap-2">
            {data.tech_stack.map((t, i) => <Tag key={i} color="#3b82f6">{t}</Tag>)}
          </div>
        </div>
      )}

      {/* Key executives */}
      {data.key_executives?.length > 0 && (
        <div className="bg-white border border-slate-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Key Executives</p>
          <div className="space-y-2">
            {data.key_executives.map((e, i) => (
              <div key={i} className="flex items-center space-x-3 py-2 border-b border-slate-50 last:border-0">
                <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <Users size={12} className="text-blue-500" />
                </div>
                <p className="text-sm text-slate-700">{e}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Two-column: competitors + customer segments */}
      <div className="grid grid-cols-2 gap-4">
        {data.main_competitors?.length > 0 && (
          <div className="bg-white border border-slate-100 rounded-2xl p-5">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Main Competitors</p>
            <div className="flex flex-wrap gap-2">
              {data.main_competitors.map((c, i) => <Tag key={i} color="#94a3b8">{c}</Tag>)}
            </div>
          </div>
        )}
        {data.customer_segments?.length > 0 && (
          <div className="bg-white border border-slate-100 rounded-2xl p-5">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Customer Segments</p>
            <div className="flex flex-wrap gap-2">
              {data.customer_segments.map((s, i) => <Tag key={i} color="#8b5cf6">{s}</Tag>)}
            </div>
          </div>
        )}
      </div>

      {/* Geographic presence */}
      {data.geographic_presence?.length > 0 && (
        <div className="bg-white border border-slate-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Geographic Presence</p>
          <div className="flex flex-wrap gap-2">
            {data.geographic_presence.map((g, i) => <Tag key={i} color="#10b981">{g}</Tag>)}
          </div>
        </div>
      )}

      {/* Recent developments */}
      {data.recent_news?.length > 0 && (
        <div className="bg-white border border-slate-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Recent Developments</p>
          <ul className="space-y-2">
            {data.recent_news.map((n, i) => (
              <li key={i} className="flex items-start space-x-2 text-sm text-slate-700">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 mt-2 flex-shrink-0" />
                <span>{n}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Market position */}
      <div className="bg-blue-50 border border-blue-100 rounded-2xl p-5">
        <p className="text-[10px] font-black text-blue-400 uppercase tracking-widest mb-2">Market Position</p>
        <p className="text-sm text-slate-700 leading-relaxed">{data.market_position}</p>
      </div>

      {/* Sources */}
      {data.sources?.filter(Boolean).length > 0 && (
        <div className="bg-slate-50 border border-slate-100 rounded-xl p-4">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Intelligence Sources</p>
          <ul className="space-y-1">
            {data.sources.filter(Boolean).slice(0, 5).map((s, i) => (
              <li key={i} className="text-[11px] text-blue-500 truncate">{s}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function QualificationData({ data }) {
  const coreChecks = [
    { label: 'SOC 2 Type II', value: data.soc2_status, ok: data.soc2_status?.toLowerCase().includes('verified') },
    { label: 'ISO 27001',     value: data.iso27001,    ok: data.iso27001?.toLowerCase().includes('certified') },
    { label: 'GDPR',          value: data.gdpr_compliant ? 'Compliant' : 'Non-Compliant', ok: data.gdpr_compliant },
    { label: 'CCPA',          value: data.ccpa_compliant ? 'Compliant' : 'Non-Compliant', ok: data.ccpa_compliant },
    { label: 'HIPAA',         value: data.hipaa_compliant ? 'Compliant' : 'Not Applicable', ok: data.hipaa_compliant },
    { label: 'PCI-DSS',       value: data.pci_dss || 'Not Applicable', ok: true },
  ];
  const esgPillars = [
    { label: 'Environmental', value: data.esg_environmental || '—' },
    { label: 'Social',        value: data.esg_social        || '—' },
    { label: 'Governance',    value: data.esg_governance    || '—' },
    { label: 'Overall',       value: `Grade ${data.esg_grade}` },
  ];
  return (
    <div className="space-y-5">
      {/* Compliance status banner */}
      <div className="bg-emerald-50 border border-emerald-100 rounded-2xl p-5">
        <p className="text-[10px] font-black text-emerald-500 uppercase tracking-widest mb-2">Overall Compliance Posture</p>
        <p className="text-sm text-slate-700 leading-relaxed">{data.compliance_notes}</p>
      </div>

      {/* Core compliance grid */}
      <div className="bg-white border border-slate-100 rounded-2xl p-5">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Regulatory Compliance Status</p>
        <div className="grid grid-cols-2 gap-3">
          {coreChecks.map(({ label, value, ok }) => (
            <div key={label} className="flex items-center space-x-3 p-3 rounded-xl bg-slate-50">
              {ok ? <CheckCircle2 size={16} className="text-emerald-500 flex-shrink-0" />
                  : <XCircle     size={16} className="text-red-400 flex-shrink-0" />}
              <div>
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{label}</p>
                <p className="text-xs font-bold text-slate-800 mt-0.5">{value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* SOC 2 details */}
      <div className="bg-white border border-slate-100 rounded-2xl p-5">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">SOC 2 Audit Details</p>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-slate-50 rounded-xl p-3">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Last Audit</p>
            <p className="text-sm font-bold text-slate-800">{data.last_audit_date || '—'}</p>
          </div>
          <div className="bg-slate-50 rounded-xl p-3">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Next Audit</p>
            <p className="text-sm font-bold text-slate-800">{data.next_audit_date || '—'}</p>
          </div>
        </div>
        {data.soc2_scope && (
          <div className="mt-3 bg-slate-50 rounded-xl p-3">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Audit Scope</p>
            <p className="text-xs text-slate-700 leading-relaxed">{data.soc2_scope}</p>
          </div>
        )}
        {data.audit_findings && (
          <div className="mt-3 bg-amber-50 border border-amber-100 rounded-xl p-3">
            <p className="text-[10px] font-black text-amber-500 uppercase tracking-widest mb-1">Audit Findings</p>
            <p className="text-xs text-amber-900">{data.audit_findings}</p>
          </div>
        )}
        {data.remediation_status && (
          <div className="mt-2 bg-emerald-50 border border-emerald-100 rounded-xl p-3">
            <p className="text-[10px] font-black text-emerald-500 uppercase tracking-widest mb-1">Remediation Status</p>
            <p className="text-xs text-emerald-800">{data.remediation_status}</p>
          </div>
        )}
      </div>

      {/* ESG breakdown */}
      <div className="bg-white border border-slate-100 rounded-2xl p-5">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">ESG Score Breakdown</p>
        <div className="grid grid-cols-4 gap-3">
          {esgPillars.map(({ label, value }) => (
            <div key={label} className="bg-emerald-50 rounded-xl p-3 text-center">
              <p className="text-[9px] font-black text-emerald-500 uppercase tracking-widest">{label}</p>
              <p className="text-xl font-black text-emerald-800 mt-1">{value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Certifications */}
      {data.certifications?.length > 0 && (
        <div className="bg-white border border-slate-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Active Certifications</p>
          <div className="flex flex-wrap gap-2">
            {data.certifications.map((c, i) => <Tag key={i} color="#8b5cf6">{c}</Tag>)}
          </div>
        </div>
      )}

      {/* Security programmes */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white border border-slate-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Penetration Testing</p>
          <p className="text-xs text-slate-700 leading-relaxed">{data.pentest_status || '—'}</p>
        </div>
        <div className="bg-white border border-slate-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Bug Bounty Programme</p>
          <p className="text-xs text-slate-700 leading-relaxed">{data.bug_bounty || '—'}</p>
        </div>
      </div>

      {/* Sub-processors */}
      {data.sub_processors?.length > 0 && (
        <div className="bg-white border border-slate-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Approved Sub-Processors</p>
          <ul className="space-y-2">
            {data.sub_processors.map((s, i) => (
              <li key={i} className="flex items-start space-x-2 text-xs text-slate-700">
                <span className="w-1.5 h-1.5 rounded-full bg-purple-400 mt-1.5 flex-shrink-0" />
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Data residency */}
      {data.data_residency && (
        <div className="bg-slate-800 rounded-2xl p-5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Data Residency</p>
          <p className="text-sm text-white leading-relaxed">{data.data_residency}</p>
        </div>
      )}
    </div>
  );
}

function RiskData({ data }) {
  const lc = data.level === 'HIGH' ? '#ef4444' : data.level === 'MEDIUM' ? '#f59e0b' : '#10b981';
  const subScores = [
    { label: 'Financial Risk',   score: data.financial_risk_score,   color: '#3b82f6' },
    { label: 'Cyber Risk',       score: data.cyber_risk_score,       color: '#8b5cf6' },
    { label: 'Operational Risk', score: data.operational_risk_score, color: '#f59e0b' },
  ];
  return (
    <div className="space-y-5">
      {/* Risk score banner */}
      <div className="rounded-2xl p-6 flex items-center justify-between" style={{ background: '#0f172a' }}>
        <div>
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Overall Risk Score</p>
          <div className="flex items-end space-x-2">
            <p className="text-5xl font-black" style={{ color: lc }}>{data.score}</p>
            <p className="text-slate-500 text-lg mb-1">/10</p>
          </div>
          <p className="font-black text-sm mt-1" style={{ color: lc }}>{data.level} RISK</p>
        </div>
        <div className="text-right">
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1">Security Rating</p>
          <p className="text-4xl font-black text-white">{data.security_rating}</p>
          <p className="text-xs text-slate-500 mt-1">{data.financial_stability}</p>
        </div>
      </div>

      {/* Sub-score breakdown */}
      <div className="grid grid-cols-3 gap-3">
        {subScores.map(({ label, score, color }) => (
          <div key={label} className="bg-white border border-slate-100 rounded-2xl p-4 text-center">
            <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-2">{label}</p>
            <p className="text-2xl font-black" style={{ color }}>{score ?? '—'}</p>
            <p className="text-[10px] text-slate-400 mt-0.5">/10</p>
            <div className="mt-2 h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div className="h-full rounded-full" style={{ width: `${((score ?? 0) / 10) * 100}%`, background: color }} />
            </div>
          </div>
        ))}
      </div>

      {/* Financial intelligence */}
      <div className="bg-white border border-slate-100 rounded-2xl p-5">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Financial Intelligence</p>
        <div className="grid grid-cols-2 gap-3">
          {[
            { label: 'Credit Rating',     value: data.credit_rating },
            { label: 'Revenue Trend',     value: data.revenue_trend },
            { label: 'YoY Growth',        value: data.revenue_growth_yoy },
            { label: 'Debt Ratio',        value: data.debt_ratio },
            { label: 'Cash Position',     value: data.cash_position },
            { label: 'Financial Stability', value: data.financial_stability },
          ].map(({ label, value }) => (
            <div key={label} className="bg-slate-50 rounded-xl p-3">
              <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">{label}</p>
              <p className="text-xs font-bold text-slate-800">{value || '—'}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Cyber security */}
      <div className="bg-white border border-slate-100 rounded-2xl p-5">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Cybersecurity Profile</p>
        <div className="space-y-3">
          {[
            { label: 'CVE History',    value: data.cve_history },
            { label: 'Patch Cadence',  value: data.patch_cadence },
          ].map(({ label, value }) => (
            <div key={label} className="bg-slate-50 rounded-xl p-3">
              <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">{label}</p>
              <p className="text-xs text-slate-700">{value || '—'}</p>
            </div>
          ))}
        </div>
        {data.incident_history?.length > 0 && (
          <div className="mt-3 bg-slate-50 rounded-xl p-3">
            <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-2">Incident History</p>
            <ul className="space-y-1.5">
              {data.incident_history.map((inc, i) => (
                <li key={i} className="flex items-start space-x-2 text-xs text-slate-700">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 mt-1.5 flex-shrink-0" />
                  <span>{inc}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Operational risk */}
      <div className="bg-white border border-slate-100 rounded-2xl p-5">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Operational Risk Factors</p>
        <div className="grid grid-cols-2 gap-3">
          {[
            { label: 'Key Person Risk',   value: data.key_person_risk },
            { label: 'Geographic Conc.',  value: data.geographic_concentration },
            { label: 'Supply Chain',      value: data.supply_chain_risk },
            { label: 'Regulatory Risk',   value: data.regulatory_risk },
          ].map(({ label, value }) => (
            <div key={label} className="bg-slate-50 rounded-xl p-3">
              <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">{label}</p>
              <p className="text-xs text-slate-700">{value || '—'}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Risk factors */}
      {data.risk_factors?.length > 0 && (
        <div className="bg-amber-50 border border-amber-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-amber-500 uppercase tracking-widest mb-3">Identified Risk Factors</p>
          <ul className="space-y-2">
            {data.risk_factors.map((f, i) => (
              <li key={i} className="flex items-start space-x-2 text-sm text-amber-900">
                <AlertTriangle size={14} className="text-amber-400 mt-0.5 flex-shrink-0" />
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Risk mitigation actions */}
      {data.risk_mitigation?.length > 0 && (
        <div className="bg-white border border-slate-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Recommended Mitigations</p>
          <ul className="space-y-2">
            {data.risk_mitigation.map((m, i) => (
              <li key={i} className="flex items-start space-x-2 text-sm text-slate-700">
                <CheckCircle2 size={14} className="text-emerald-500 mt-0.5 flex-shrink-0" />
                <span>{m}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Industry benchmark */}
      {data.industry_benchmark && (
        <div className="bg-slate-800 rounded-2xl p-5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Industry Benchmark</p>
          <p className="text-sm text-white leading-relaxed">{data.industry_benchmark}</p>
        </div>
      )}

      {/* Monitoring hooks */}
      <div className="grid grid-cols-2 gap-4">
        {[
          { label: 'Cyber Monitoring',     hook: data.cyber_monitoring,     color: '#8b5cf6' },
          { label: 'Financial Monitoring', hook: data.financial_monitoring, color: '#3b82f6' },
        ].map(({ label, hook, color }) => hook?.status && (
          <div key={label} className="bg-white border border-slate-100 rounded-2xl p-4">
            <div className="flex items-center justify-between mb-3">
              <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{label}</p>
              <span className="text-[9px] font-black px-2 py-0.5 rounded-full"
                style={{ background: color + '18', color }}>
                {hook.status}
              </span>
            </div>
            <p className="text-[10px] text-slate-500 mb-1"><span className="font-bold">Provider:</span> {hook.provider}</p>
            <p className="text-[10px] text-slate-500 mb-2"><span className="font-bold">Cadence:</span> {hook.cadence}</p>
            {hook.signals?.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {hook.signals.map((s, i) => (
                  <span key={i} className="text-[9px] px-1.5 py-0.5 bg-slate-100 rounded text-slate-500">{s}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Recommendation */}
      <div className="bg-emerald-50 border border-emerald-100 rounded-2xl p-5">
        <p className="text-[10px] font-black text-emerald-500 uppercase tracking-widest mb-2">Analyst Recommendation</p>
        <p className="text-sm text-slate-700 leading-relaxed">{data.recommendation}</p>
      </div>
    </div>
  );
}

function ContractData({ data }) {
  const priorityColor = { High: '#ef4444', Medium: '#f59e0b', Low: '#10b981' };
  return (
    <div className="space-y-5">
      {/* Contract status banner */}
      <div className="bg-emerald-50 border border-emerald-100 rounded-2xl p-5 flex items-center justify-between">
        <div>
          <p className="text-[10px] font-black text-emerald-500 uppercase tracking-widest mb-1">MSA Status</p>
          <p className="text-base font-black text-slate-800">{data.msa_status}</p>
        </div>
        <div className="bg-emerald-100 rounded-xl px-4 py-2 text-center">
          <p className="text-[9px] font-black text-emerald-600 uppercase tracking-widest">Projected Savings</p>
          <p className="text-sm font-black text-emerald-800 mt-0.5">{data.savings_opportunity}</p>
        </div>
      </div>

      {/* Core terms KPI */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Term',      value: data.suggested_term },
          { label: 'Payment',   value: data.payment_terms },
          { label: 'SLA',       value: data.sla_uptime },
          { label: 'Notice',    value: data.termination_notice },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white border border-slate-100 rounded-xl p-3 text-center">
            <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{label}</p>
            <p className="text-xs font-black text-slate-800 mt-1 leading-tight">{value || '—'}</p>
          </div>
        ))}
      </div>

      {/* Price protection highlight */}
      {data.price_protection && (
        <div className="bg-emerald-50 border-l-4 border-emerald-500 rounded-r-2xl p-5 flex items-start space-x-3">
          <Zap size={18} className="text-emerald-500 mt-0.5 flex-shrink-0" fill="currentColor" />
          <div>
            <p className="text-[10px] font-black text-emerald-600 uppercase tracking-widest mb-1">Price Protection Clause</p>
            <p className="text-sm text-emerald-800 leading-relaxed">{data.price_protection}</p>
          </div>
        </div>
      )}

      {/* SLA details */}
      <div className="bg-white border border-slate-100 rounded-2xl p-5">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">SLA Details</p>
        <div className="space-y-3">
          <div className="bg-slate-50 rounded-xl p-3">
            <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Response Times</p>
            <p className="text-xs text-slate-700">{data.sla_response_time || '—'}</p>
          </div>
          <div className="bg-slate-50 rounded-xl p-3">
            <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Service Credits</p>
            <p className="text-xs text-slate-700">{data.sla_credits || '—'}</p>
          </div>
        </div>
      </div>

      {/* Key clauses */}
      {data.key_clauses?.length > 0 && (
        <div className="bg-white border border-slate-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Key Contract Clauses</p>
          <ul className="space-y-2">
            {data.key_clauses.map((c, i) => (
              <li key={i} className="flex items-start space-x-2 text-sm text-slate-700">
                <CheckCircle2 size={14} className="text-emerald-500 mt-0.5 flex-shrink-0" />
                <span>{c}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Additional legal terms */}
      <div className="bg-white border border-slate-100 rounded-2xl p-5">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Legal & Operational Terms</p>
        <div className="space-y-3">
          {[
            { label: 'Liability Cap',       value: data.liability_cap },
            { label: 'IP Ownership',        value: data.ip_ownership },
            { label: 'Auto-Renewal',        value: data.auto_renewal_terms },
            { label: 'Data Portability',    value: data.data_portability },
            { label: 'Governing Law',       value: data.governing_law },
            { label: 'Dispute Resolution',  value: data.dispute_resolution },
            { label: 'Audit Rights',        value: data.audit_rights },
            { label: 'Exit Assistance',     value: data.exit_assistance },
            { label: 'Sub-processor Rights', value: data.subcontractor_rights },
          ].map(({ label, value }) => value && (
            <div key={label} className="border-b border-slate-50 pb-3 last:border-0 last:pb-0">
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{label}</p>
              <p className="text-xs text-slate-700 leading-relaxed">{value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Negotiation blueprint */}
      {data.negotiation_blueprint?.length > 0 && (
        <div className="bg-white border border-slate-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Negotiation Blueprint</p>
          <div className="space-y-4">
            {data.negotiation_blueprint.map((pt, i) => (
              <div key={i} className="border border-slate-100 rounded-xl overflow-hidden">
                <div className="flex items-center justify-between px-4 py-2.5 bg-slate-50 border-b border-slate-100">
                  <p className="text-xs font-black text-slate-700 uppercase tracking-wide">{pt.clause}</p>
                  {pt.priority && (
                    <span className="text-[9px] font-black px-2 py-0.5 rounded-full"
                      style={{ background: (priorityColor[pt.priority] || '#94a3b8') + '18', color: priorityColor[pt.priority] || '#94a3b8' }}>
                      {pt.priority} Priority
                    </span>
                  )}
                </div>
                <div className="p-4 space-y-2">
                  <div>
                    <p className="text-[9px] font-black text-red-400 uppercase tracking-widest mb-0.5">Current</p>
                    <p className="text-xs text-slate-600">{pt.current}</p>
                  </div>
                  <div>
                    <p className="text-[9px] font-black text-emerald-500 uppercase tracking-widest mb-0.5">Target</p>
                    <p className="text-xs font-bold text-emerald-700">{pt.target}</p>
                  </div>
                  <div>
                    <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-0.5">Rationale</p>
                    <p className="text-xs text-slate-600">{pt.rationale}</p>
                  </div>
                  {pt.talking_point && (
                    <div className="bg-blue-50 rounded-lg p-2.5 mt-1">
                      <p className="text-[9px] font-black text-blue-400 uppercase tracking-widest mb-0.5">Talking Point</p>
                      <p className="text-xs text-blue-800 italic">"{pt.talking_point}"</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Savings breakdown */}
      {data.savings_breakdown?.length > 0 && (
        <div className="bg-blue-50 border border-blue-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-blue-500 uppercase tracking-widest mb-3">Savings Breakdown</p>
          <ul className="space-y-2">
            {data.savings_breakdown.map((s, i) => (
              <li key={i} className="flex items-start space-x-2 text-sm text-blue-800">
                <DollarSign size={14} className="text-blue-400 mt-0.5 flex-shrink-0" />
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function DecisionData({ data }) {
  const map    = { GO: '#10b981', CONDITIONAL_GO: '#f59e0b', NO_GO: '#ef4444' };
  const color  = map[data.verdict] || '#10b981';
  const statusColor = { PASS: '#10b981', WARN: '#f59e0b', FAIL: '#ef4444' };
  return (
    <div className="space-y-5">
      {/* Verdict banner */}
      <div className="rounded-2xl p-8 text-center" style={{ background: '#0f172a', boxShadow: `0 0 50px ${color}25` }}>
        <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">System Verdict</p>
        <p className="text-5xl font-black tracking-wide" style={{ color }}>{data.verdict?.replace(/_/g, ' ')}</p>
        {data.total_savings && data.verdict !== 'NO_GO' && (
          <p className="text-emerald-400 text-sm font-black mt-3">{data.total_savings}</p>
        )}
      </div>

      {/* Executive summary */}
      <div className="bg-white border border-slate-100 rounded-2xl p-5">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Executive Summary</p>
        <p className="text-sm text-slate-700 italic leading-relaxed">"{data.summary}"</p>
      </div>

      {/* Scorecard */}
      {data.scorecard?.length > 0 && (
        <div className="bg-white border border-slate-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-4">Decision Scorecard</p>
          <div className="space-y-2">
            {data.scorecard.map((row, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-slate-50 last:border-0">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-2 rounded-full flex-shrink-0"
                    style={{ background: statusColor[row.status] || '#94a3b8' }} />
                  <p className="text-sm font-bold text-slate-700">{row.criterion}</p>
                </div>
                <div className="flex items-center space-x-3">
                  <p className="text-xs text-slate-500 text-right max-w-[180px]">{row.detail}</p>
                  <span className="text-[10px] font-black px-2 py-0.5 rounded-full flex-shrink-0"
                    style={{ background: (statusColor[row.status] || '#94a3b8') + '18', color: statusColor[row.status] || '#94a3b8' }}>
                    {row.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Aggregated logic */}
      {data.aggregated_logic && (
        <div className="bg-slate-50 border border-slate-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Aggregated Decision Logic</p>
          <p className="text-sm text-slate-700 leading-relaxed">{data.aggregated_logic}</p>
        </div>
      )}

      {/* Conditions (CONDITIONAL_GO) */}
      {data.conditions?.length > 0 && (
        <div className="bg-amber-50 border border-amber-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-amber-500 uppercase tracking-widest mb-3">Conditions to Satisfy</p>
          <ul className="space-y-2">
            {data.conditions.map((c, i) => (
              <li key={i} className="flex items-start space-x-2 text-sm text-amber-900">
                <AlertTriangle size={14} className="text-amber-400 mt-0.5 flex-shrink-0" />
                <span>{c}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Next steps */}
      {data.next_steps?.length > 0 && (
        <div className="bg-white border border-slate-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Required Next Steps</p>
          <ol className="space-y-2">
            {data.next_steps.map((s, i) => (
              <li key={i} className="flex items-start space-x-3 text-sm text-slate-700">
                <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-600 text-[10px] font-black flex items-center justify-center flex-shrink-0 mt-0.5">
                  {i + 1}
                </span>
                <span>{s}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Approvals + timeline */}
      <div className="grid grid-cols-2 gap-4">
        {data.required_approvals?.length > 0 && (
          <div className="bg-white border border-slate-100 rounded-2xl p-5">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Required Approvals</p>
            <ul className="space-y-1.5">
              {data.required_approvals.map((a, i) => (
                <li key={i} className="flex items-center space-x-2 text-xs text-slate-700">
                  <CheckSquare size={12} className="text-blue-400 flex-shrink-0" />
                  <span>{a}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        <div className="space-y-3">
          {data.onboarding_timeline && (
            <div className="bg-white border border-slate-100 rounded-2xl p-4">
              <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Onboarding Timeline</p>
              <p className="text-sm font-bold text-slate-800">{data.onboarding_timeline}</p>
            </div>
          )}
          {data.review_checkpoint && (
            <div className="bg-white border border-slate-100 rounded-2xl p-4">
              <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Review Checkpoint</p>
              <p className="text-sm font-bold text-slate-800">{data.review_checkpoint}</p>
            </div>
          )}
        </div>
      </div>

      {/* Integration notes */}
      {data.integration_notes && (
        <div className="bg-blue-50 border border-blue-100 rounded-2xl p-5">
          <p className="text-[10px] font-black text-blue-400 uppercase tracking-widest mb-2">Integration Notes</p>
          <p className="text-sm text-blue-900 leading-relaxed">{data.integration_notes}</p>
        </div>
      )}
    </div>
  );
}

// ── ValidationGate — reusable gate component ──────────────────────────────────

function ValidationGate({ stepMeta, data, onContinue, onCancel, isLast, verdict }) {
  const Icon     = stepMeta.icon;
  const isNoGo   = verdict === 'NO_GO';
  const contLabel = isLast
    ? (isNoGo ? 'Acknowledged — Do Not Onboard' : 'Approve & Onboard Vendor')
    : 'Confirm & Continue';

  return (
    <div>
      {/* Gate header */}
      <div className="flex items-center space-x-4 mb-6 pb-5 border-b border-slate-100">
        <div className="w-11 h-11 rounded-2xl flex items-center justify-center flex-shrink-0"
          style={{ background: stepMeta.bg }}>
          <Icon size={22} style={{ color: stepMeta.color }} />
        </div>
        <div>
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
            Data Retrieved — Awaiting Your Review
          </p>
          <h3 className="text-base font-black text-slate-900 mt-0.5">{stepMeta.label}</h3>
        </div>
        <div className="ml-auto">
          <span className="text-[10px] font-black px-3 py-1.5 rounded-full uppercase tracking-widest"
            style={{ background: stepMeta.color + '18', color: stepMeta.color }}>
            {stepMeta.agent}
          </span>
        </div>
      </div>

      {/* Fetched data */}
      <div className="mb-6">
        {stepMeta.key === 'discovery'     && <DiscoveryData     data={data} />}
        {stepMeta.key === 'qualification' && <QualificationData data={data} />}
        {stepMeta.key === 'risk'          && <RiskData          data={data} />}
        {stepMeta.key === 'contract'      && <ContractData      data={data} />}
        {stepMeta.key === 'decision'      && <DecisionData      data={data} />}
      </div>

      {/* Action buttons — the explicit user gate */}
      <div className="flex space-x-3 pt-5 border-t border-slate-100">
        <button
          onClick={onCancel}
          className="flex items-center justify-center space-x-2 px-5 py-3.5 rounded-xl border-2 border-slate-200 text-slate-500 font-black text-xs uppercase tracking-widest hover:bg-red-50 hover:border-red-200 hover:text-red-600 transition-all"
        >
          <Ban size={14} />
          <span>Cancel</span>
        </button>
        <button
          onClick={onContinue}
          className="flex-1 flex items-center justify-center space-x-2 py-3.5 rounded-xl text-white font-black text-xs uppercase tracking-widest transition-all"
          style={{
            background:  isNoGo ? '#64748b' : stepMeta.color,
            boxShadow:   isNoGo ? 'none' : `0 0 20px ${stepMeta.color}40`,
          }}
        >
          <CheckSquare size={15} />
          <span>{contLabel}</span>
        </button>
      </div>
    </div>
  );
}

// ── Step progress tracker ─────────────────────────────────────────────────────

function StepTracker({ steps, currentIndex, phase, completedKeys }) {
  return (
    <div className="flex items-center justify-between mb-8 px-2">
      {steps.map((s, i) => {
        const Icon      = s.icon;
        const done      = completedKeys.includes(s.key);
        const active    = i === currentIndex;
        const pending   = i > currentIndex;
        const isLast    = i === steps.length - 1;

        return (
          <React.Fragment key={s.key}>
            <div className="flex flex-col items-center">
              <div
                className="w-10 h-10 rounded-2xl flex items-center justify-center transition-all duration-300"
                style={{
                  background: done   ? s.color
                            : active ? s.bg
                            :          '#f1f5f9',
                  boxShadow: active ? `0 0 0 3px ${s.color}30` : 'none',
                }}
              >
                {done
                  ? <CheckCircle2 size={18} color="#fff" />
                  : <Icon size={18} style={{ color: active ? s.color : '#94a3b8' }} />
                }
              </div>
              <p className="text-[9px] font-black mt-1.5 text-center uppercase tracking-wider"
                style={{ color: done || active ? s.color : '#94a3b8', maxWidth: 60 }}>
                {s.label.split(' ')[0]}
              </p>
            </div>
            {!isLast && (
              <div className="flex-1 h-0.5 mx-1 rounded-full transition-all duration-500"
                style={{ background: done ? s.color : '#e2e8f0' }} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

// ── Fetching skeleton ─────────────────────────────────────────────────────────

function FetchingState({ stepMeta }) {
  const Icon = stepMeta?.icon || Search;
  return (
    <div className="flex flex-col items-center justify-center h-full py-20 space-y-6">
      <div className="relative">
        <div className="w-20 h-20 rounded-3xl flex items-center justify-center"
          style={{ background: stepMeta?.bg || '#eff6ff' }}>
          <Icon size={36} style={{ color: stepMeta?.color || '#3b82f6' }} />
        </div>
        <div className="absolute -bottom-1 -right-1 w-7 h-7 bg-white rounded-full border-2 border-slate-100 flex items-center justify-center">
          <Loader2 size={14} className="animate-spin" style={{ color: stepMeta?.color || '#3b82f6' }} />
        </div>
      </div>
      <div className="text-center">
        <p className="font-black text-slate-800 text-base">{stepMeta?.label}</p>
        <p className="text-slate-400 text-sm mt-1">{stepMeta?.agent} is running...</p>
        <p className="text-slate-300 text-xs mt-1">{stepMeta?.description}</p>
      </div>
      <div className="w-48 space-y-2 mt-4">
        {[80, 60, 70].map((w, i) => (
          <div key={i} className="h-2 rounded-full bg-slate-100 overflow-hidden">
            <div className="h-full rounded-full animate-pulse" style={{ width: `${w}%`, background: stepMeta?.color + '40' || '#3b82f640' }} />
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Cancelled state ───────────────────────────────────────────────────────────

function CancelledState({ stepMeta, onAbort, auditLog }) {
  return (
    <div className="flex flex-col items-center justify-center h-full py-16 space-y-6">
      <div className="w-20 h-20 bg-red-50 rounded-3xl flex items-center justify-center">
        <Ban size={36} className="text-red-400" />
      </div>
      <div className="text-center">
        <h3 className="font-black text-slate-900 text-xl">Workflow Cancelled</h3>
        <p className="text-slate-500 text-sm mt-2">
          Cancelled at <span className="font-bold">{stepMeta?.label}</span>.
          No vendor was onboarded.
        </p>
      </div>
      <div className="w-full max-w-sm bg-white border border-slate-100 rounded-2xl p-4">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Audit Trail</p>
        <div className="space-y-1.5 max-h-32 overflow-y-auto">
          {auditLog.map((e, i) => (
            <div key={i} className="flex items-center space-x-2 text-xs">
              <span className="font-black px-2 py-0.5 rounded text-[10px]"
                style={{
                  background: e.event === 'USER_CANCELLED' ? '#fef2f2' : '#f8fafc',
                  color:      e.event === 'USER_CANCELLED' ? '#ef4444' : '#64748b',
                }}>
                {e.event}
              </span>
              <span className="text-slate-400">{e.step}</span>
              <span className="text-slate-300 ml-auto">{new Date(e.ts).toLocaleTimeString()}</span>
            </div>
          ))}
        </div>
      </div>
      <button
        onClick={onAbort}
        className="flex items-center space-x-2 px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl font-black text-xs uppercase tracking-widest transition-all"
      >
        <RotateCcw size={14} />
        <span>Back to Dashboard</span>
      </button>
    </div>
  );
}

// ── Completed state ───────────────────────────────────────────────────────────

function CompletedState({ decisionData, auditLog, onAbort }) {
  const isNoGo = decisionData?.verdict === 'NO_GO';
  const color  = isNoGo ? '#ef4444' : decisionData?.verdict === 'CONDITIONAL_GO' ? '#f59e0b' : '#10b981';

  return (
    <div className="flex flex-col items-center justify-center h-full py-10 space-y-6">
      <div className="w-20 h-20 rounded-3xl flex items-center justify-center"
        style={{ background: color + '18', boxShadow: `0 0 30px ${color}30` }}>
        {isNoGo
          ? <XCircle size={36} style={{ color }} />
          : <CheckCircle2 size={36} style={{ color }} />}
      </div>
      <div className="text-center">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Workflow Complete</p>
        <h3 className="font-black text-2xl" style={{ color }}>
          {decisionData?.verdict?.replace(/_/g, ' ')}
        </h3>
        {!isNoGo && (
          <p className="text-emerald-600 text-xs font-black uppercase tracking-widest mt-1">
            Vendor added to production registry
          </p>
        )}
      </div>
      {decisionData?.total_savings && !isNoGo && (
        <div className="bg-emerald-50 border border-emerald-100 rounded-2xl px-6 py-4 text-center">
          <p className="text-[10px] font-black text-emerald-500 uppercase tracking-widest mb-1">Projected Savings</p>
          <p className="text-sm font-black text-emerald-800">{decisionData.total_savings}</p>
        </div>
      )}
      <div className="w-full max-w-md bg-white border border-slate-100 rounded-2xl p-4">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Full Audit Trail</p>
        <div className="space-y-1.5 max-h-40 overflow-y-auto">
          {auditLog.map((e, i) => (
            <div key={i} className="flex items-center space-x-2 text-xs">
              <span className="font-black px-2 py-0.5 rounded text-[10px] flex-shrink-0"
                style={{
                  background: e.event.includes('CANCEL') ? '#fef2f2'
                            : e.event.includes('CONTINUE') ? '#f0fdf4'
                            : e.event.includes('FETCHED') ? '#eff6ff'
                            : '#f8fafc',
                  color:      e.event.includes('CANCEL') ? '#ef4444'
                            : e.event.includes('CONTINUE') ? '#10b981'
                            : e.event.includes('FETCHED') ? '#3b82f6'
                            : '#64748b',
                }}>
                {e.event}
              </span>
              <span className="text-slate-500 font-bold">{e.step}</span>
              <span className="text-slate-300 ml-auto flex-shrink-0">{new Date(e.ts).toLocaleTimeString()}</span>
            </div>
          ))}
        </div>
      </div>
      <button
        onClick={onAbort}
        className="flex items-center space-x-2 px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl font-black text-xs uppercase tracking-widest transition-all"
      >
        <ChevronRight size={14} />
        <span>Return to Dashboard</span>
      </button>
    </div>
  );
}

// ── Live audit strip ──────────────────────────────────────────────────────────

function AuditStrip({ logs }) {
  const last = logs.slice(-4);
  const eventColor = (e) =>
    e.includes('CANCEL')   ? { bg: '#fef2f2', text: '#ef4444' }
  : e.includes('CONTINUE') ? { bg: '#f0fdf4', text: '#10b981' }
  : e.includes('FETCHED')  ? { bg: '#eff6ff', text: '#3b82f6' }
  : e.includes('STARTED')  ? { bg: '#f5f3ff', text: '#8b5cf6' }
  :                          { bg: '#f8fafc',  text: '#64748b' };

  if (!last.length) return null;
  return (
    <div className="border-t border-slate-100 px-6 py-3 flex items-center space-x-4 bg-slate-50 flex-shrink-0">
      <div className="flex items-center space-x-1.5 text-slate-400 flex-shrink-0">
        <Clock size={11} />
        <span className="text-[10px] font-black uppercase tracking-widest">Audit Log</span>
      </div>
      <div className="flex items-center space-x-2 overflow-x-auto">
        {last.map((e, i) => {
          const c = eventColor(e.event);
          return (
            <div key={i} className="flex items-center space-x-1.5 flex-shrink-0">
              <span className="text-[10px] font-black px-2 py-0.5 rounded"
                style={{ background: c.bg, color: c.text }}>
                {e.event}
              </span>
              {e.step && <span className="text-[10px] text-slate-400 font-bold">{e.step}</span>}
              <span className="text-[10px] text-slate-300">{new Date(e.ts).toLocaleTimeString()}</span>
              {i < last.length - 1 && <span className="text-slate-200 mx-1">|</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Error state ───────────────────────────────────────────────────────────────

function ErrorState({ message, onAbort }) {
  return (
    <div className="flex flex-col items-center justify-center h-full py-20 space-y-4">
      <AlertTriangle size={40} className="text-red-400" />
      <p className="font-black text-slate-800">Connection Error</p>
      <p className="text-slate-500 text-sm text-center max-w-xs">{message}</p>
      <button onClick={onAbort}
        className="px-6 py-3 bg-slate-800 text-white rounded-xl font-black text-xs uppercase tracking-widest">
        Back to Dashboard
      </button>
    </div>
  );
}

// ── Main wizard ───────────────────────────────────────────────────────────────

export default function OnboardingWizard({ vendorName, onComplete, onAbort }) {
  const [sessionId,    setSessionId]    = useState(null);
  const [stepIndex,    setStepIndex]    = useState(-1);
  // phase: starting | fetching | reviewing | cancelled | completed
  const [phase,        setPhase]        = useState('starting');
  const [stepData,     setStepData]     = useState({});
  const [completedKeys,setCompletedKeys]= useState([]);
  const [auditLog,     setAuditLog]     = useState([]);
  const [error,        setError]        = useState(null);

  const pushLog = (event, step) =>
    setAuditLog(prev => [...prev, { event, step, ts: new Date().toISOString() }]);

  const emit = useCallback((sid, eventType, step, extra = {}) => {
    pushLog(eventType, step);
    emitLog(sid, eventType, step, extra);
  }, []);

  // ── 1. Create session on mount ────────────────────────────────────────────
  useEffect(() => {
    let dead = false;
    (async () => {
      try {
        const res  = await fetch(`${API}/sessions`, {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify({ vendor_name: vendorName }),
        });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        if (dead) return;
        setSessionId(data.id);
        pushLog('WORKFLOW_STARTED', 'discovery');
        await emitLog(data.id, 'WORKFLOW_STARTED', 'discovery', { vendor: vendorName });
        setStepIndex(0);
        setPhase('fetching');
      } catch (e) {
        if (!dead) setError('Cannot reach onboarding API at http://localhost:8090. Run: cd C:\\sourcing\\onboarding && python -m uvicorn backend.main:app --port 8090');
      }
    })();
    return () => { dead = true; };
  }, [vendorName]);

  // ── 2. Fetch step data whenever phase becomes "fetching" ──────────────────
  useEffect(() => {
    if (phase !== 'fetching' || stepIndex < 0 || !sessionId) return;
    let dead = false;
    const step = STEPS[stepIndex];

    (async () => {
      try {
        const res  = await fetch(`${API}/sessions/${sessionId}/run/${step.key}`, { method: 'POST' });
        if (!res.ok) throw new Error(await res.text());
        const data = await res.json();
        if (dead) return;
        setStepData(prev => ({ ...prev, [step.key]: data }));
        emit(sessionId, 'DATA_FETCHED', step.key, { keys: Object.keys(data) });
        setPhase('reviewing');
      } catch (e) {
        if (!dead) setError(`Failed at "${step.label}": ${e.message}`);
      }
    })();
    return () => { dead = true; };
  }, [phase, stepIndex, sessionId, emit]);

  // ── User actions ──────────────────────────────────────────────────────────

  const handleContinue = async () => {
    const step = STEPS[stepIndex];
    emit(sessionId, 'USER_CONTINUED', step.key);
    setCompletedKeys(prev => [...prev, step.key]);

    if (stepIndex === STEPS.length - 1) {
      setPhase('completed');
    } else {
      setStepIndex(prev => prev + 1);
      setPhase('fetching');
    }
  };

  const handleCancel = () => {
    const step = STEPS[stepIndex] || STEPS[0];
    emit(sessionId, 'USER_CANCELLED', step.key);
    setPhase('cancelled');
  };

  // ── Render ────────────────────────────────────────────────────────────────

  if (error) return (
    <div className="flex flex-col h-full">
      <ErrorState message={error} onAbort={onAbort} />
    </div>
  );

  if (phase === 'cancelled') return (
    <div className="flex flex-col h-full">
      <CancelledState stepMeta={STEPS[stepIndex]} onAbort={onAbort} auditLog={auditLog} />
    </div>
  );

  if (phase === 'completed') return (
    <div className="flex flex-col h-full">
      <CompletedState
        decisionData={stepData['decision']}
        auditLog={auditLog}
        onAbort={onAbort}
      />
    </div>
  );

  const currentStep = stepIndex >= 0 ? STEPS[stepIndex] : STEPS[0];

  return (
    <div className="min-h-screen bg-[#f8fafc] flex flex-col font-sans">

      {/* Top bar */}
      <div className="bg-white border-b border-slate-100 px-8 py-4 flex items-center justify-between flex-shrink-0 shadow-sm">
        <div className="flex items-center space-x-4">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Package size={16} className="text-white" />
          </div>
          <div>
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Vendor Onboarding</p>
            <h2 className="font-black text-slate-900 text-base leading-tight">{vendorName}</h2>
          </div>
        </div>
        {sessionId && (
          <p className="font-mono text-[11px] text-slate-300">Session {sessionId}</p>
        )}
      </div>

      {/* Step progress bar */}
      <div className="bg-white border-b border-slate-100 px-12 pt-6 pb-5 flex-shrink-0">
        <StepTracker
          steps={STEPS}
          currentIndex={stepIndex}
          phase={phase}
          completedKeys={completedKeys}
        />
      </div>

      {/* Full-page content area — each step is its own dedicated page */}
      <div className="flex-1 flex flex-col overflow-y-auto">
        <div className="max-w-2xl w-full mx-auto px-6 py-8 flex-1">
          {(phase === 'starting' || phase === 'fetching') && (
            <FetchingState stepMeta={currentStep} />
          )}
          {phase === 'reviewing' && stepIndex >= 0 && (
            <ValidationGate
              stepMeta={currentStep}
              data={stepData[currentStep.key]}
              onContinue={handleContinue}
              onCancel={handleCancel}
              isLast={stepIndex === STEPS.length - 1}
              verdict={stepData['decision']?.verdict}
            />
          )}
        </div>
      </div>

      {/* Audit strip — pinned to bottom */}
      <AuditStrip logs={auditLog} />
    </div>
  );
}
