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
  CheckSquare, Ban, RotateCcw, Clock, Package,
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
    <div className="space-y-4">
      <div className="bg-blue-50 border border-blue-100 rounded-2xl p-5">
        <p className="text-[10px] font-black text-blue-400 uppercase tracking-widest mb-2">Company Overview</p>
        <p className="text-sm text-slate-700 leading-relaxed">{data.company_summary}</p>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Card label="Founded"      value={data.founded}        icon={Building2}  accent="#3b82f6" />
        <Card label="Headquarters" value={data.headquarters}   icon={Globe}      accent="#3b82f6" />
        <Card label="Employees"    value={data.employees}      icon={Users}      accent="#3b82f6" />
        <Card label="Funding"      value={data.recent_funding} icon={DollarSign} accent="#3b82f6" />
      </div>
      {data.products?.length > 0 && (
        <div className="bg-white border border-slate-100 rounded-xl p-4">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Products</p>
          <div className="flex flex-wrap gap-2">
            {data.products.map((p, i) => <Tag key={i} color="#3b82f6">{p}</Tag>)}
          </div>
        </div>
      )}
      {data.market_position && (
        <div className="bg-white border border-slate-100 rounded-xl p-4">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Market Position</p>
          <p className="text-sm text-slate-700">{data.market_position}</p>
        </div>
      )}
    </div>
  );
}

function QualificationData({ data }) {
  const checks = [
    { label: 'SOC2 Status', value: data.soc2_status, ok: data.soc2_status?.toLowerCase().includes('verified') },
    { label: 'ISO 27001',   value: data.iso27001,    ok: data.iso27001?.toLowerCase().includes('certified') },
    { label: 'GDPR',        value: data.gdpr_compliant ? 'Compliant' : 'Non-Compliant', ok: data.gdpr_compliant },
    { label: 'ESG Grade',   value: `Grade ${data.esg_grade}`, ok: ['A+','A','A-','B+'].includes(data.esg_grade) },
  ];
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        {checks.map(({ label, value, ok }) => (
          <div key={label} className="bg-white border border-slate-100 rounded-xl p-4 flex items-start space-x-3">
            {ok
              ? <CheckCircle2 size={18} className="text-emerald-500 mt-0.5 flex-shrink-0" />
              : <XCircle     size={18} className="text-red-400 mt-0.5 flex-shrink-0" />}
            <div>
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-0.5">{label}</p>
              <p className="text-sm font-bold text-slate-800">{value}</p>
            </div>
          </div>
        ))}
      </div>
      {data.certifications?.length > 0 && (
        <div className="bg-white border border-slate-100 rounded-xl p-4">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Certifications</p>
          <div className="flex flex-wrap gap-2">
            {data.certifications.map((c, i) => <Tag key={i} color="#8b5cf6">{c}</Tag>)}
          </div>
        </div>
      )}
      {data.compliance_notes && (
        <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4 text-sm text-emerald-800 leading-relaxed">
          {data.compliance_notes}
        </div>
      )}
    </div>
  );
}

function RiskData({ data }) {
  const levelColor = data.level === 'HIGH' ? '#ef4444' : data.level === 'MEDIUM' ? '#f59e0b' : '#10b981';
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-white border border-slate-100 rounded-xl p-4 text-center">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Risk Score</p>
          <p className="text-3xl font-black" style={{ color: levelColor }}>
            {data.score}<span className="text-slate-300 text-sm">/10</span>
          </p>
        </div>
        <div className="bg-white border border-slate-100 rounded-xl p-4 text-center">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Level</p>
          <p className="text-lg font-black" style={{ color: levelColor }}>{data.level}</p>
        </div>
        <div className="bg-white border border-slate-100 rounded-xl p-4 text-center">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Security</p>
          <p className="text-2xl font-black text-slate-800">{data.security_rating}</p>
        </div>
      </div>
      {data.risk_factors?.length > 0 && (
        <div className="bg-white border border-slate-100 rounded-xl p-4">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Risk Factors</p>
          <ul className="space-y-2">
            {data.risk_factors.map((f, i) => (
              <li key={i} className="flex items-start space-x-2 text-sm text-slate-700">
                <AlertTriangle size={14} className="text-amber-400 mt-0.5 flex-shrink-0" />
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {data.recommendation && (
        <div className="bg-amber-50 border border-amber-100 rounded-xl p-4 text-sm text-amber-900 leading-relaxed">
          {data.recommendation}
        </div>
      )}
    </div>
  );
}

function ContractData({ data }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        {[
          { label: 'Contract Term',      value: data.suggested_term },
          { label: 'Payment Terms',      value: data.payment_terms },
          { label: 'SLA Uptime',         value: data.sla_uptime },
          { label: 'Termination Notice', value: data.termination_notice },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white border border-slate-100 rounded-xl p-4">
            <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{label}</p>
            <p className="text-sm font-bold text-slate-800">{value || '—'}</p>
          </div>
        ))}
      </div>
      {data.price_protection && (
        <div className="bg-emerald-50 border-l-4 border-emerald-400 rounded-r-xl p-4 flex items-start space-x-3">
          <Zap size={16} className="text-emerald-500 mt-0.5 flex-shrink-0" fill="currentColor" />
          <div>
            <p className="text-[10px] font-black text-emerald-600 uppercase tracking-widest mb-1">Price Protection</p>
            <p className="text-sm text-emerald-800">{data.price_protection}</p>
          </div>
        </div>
      )}
      {data.negotiation_blueprint?.length > 0 && (
        <div className="bg-white border border-slate-100 rounded-xl p-4">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-3">Negotiation Blueprint</p>
          <div className="space-y-3">
            {data.negotiation_blueprint.map((pt, i) => (
              <div key={i} className="bg-slate-50 rounded-xl p-3 border border-slate-100">
                <p className="text-xs font-black text-slate-700 uppercase tracking-wide mb-1">{pt.clause}</p>
                <p className="text-xs text-slate-500 mb-0.5"><span className="font-bold">Current:</span> {pt.current}</p>
                <p className="text-xs font-bold" style={{ color: '#10b981' }}>
                  <span className="text-slate-400 font-normal">Target: </span>{pt.target}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
      {data.savings_opportunity && (
        <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 text-sm text-blue-800 font-medium">
          <span className="font-black">Savings Opportunity: </span>{data.savings_opportunity}
        </div>
      )}
    </div>
  );
}

function DecisionData({ data }) {
  const map = { GO: '#10b981', CONDITIONAL_GO: '#f59e0b', NO_GO: '#ef4444' };
  const color = map[data.verdict] || '#10b981';
  const glow  = color + '30';
  return (
    <div className="space-y-4">
      <div className="rounded-2xl p-8 text-center" style={{ background: '#0f172a', boxShadow: `0 0 40px ${glow}` }}>
        <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">System Verdict</p>
        <p className="text-4xl font-black tracking-wide" style={{ color }}>
          {data.verdict?.replace(/_/g, ' ')}
        </p>
      </div>
      <div className="bg-white border border-slate-100 rounded-xl p-5">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Summary</p>
        <p className="text-sm text-slate-700 italic leading-relaxed">"{data.summary}"</p>
      </div>
      {data.aggregated_logic && (
        <div className="bg-white border border-slate-100 rounded-xl p-5">
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Aggregated Logic</p>
          <p className="text-sm text-slate-700 leading-relaxed">{data.aggregated_logic}</p>
        </div>
      )}
      {data.total_savings && (
        <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4 text-sm text-emerald-800 font-bold">
          {data.total_savings}
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
    <div className="flex flex-col h-full">
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
      <div className="flex-1 overflow-y-auto pr-1 space-y-1">
        {stepMeta.key === 'discovery'     && <DiscoveryData     data={data} />}
        {stepMeta.key === 'qualification' && <QualificationData data={data} />}
        {stepMeta.key === 'risk'          && <RiskData          data={data} />}
        {stepMeta.key === 'contract'      && <ContractData      data={data} />}
        {stepMeta.key === 'decision'      && <DecisionData      data={data} />}
      </div>

      {/* Action buttons — the explicit user gate */}
      <div className="flex space-x-3 mt-6 pt-5 border-t border-slate-100 flex-shrink-0">
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
    <div className="flex flex-col h-full bg-[#f8fafc]">
      {/* Header */}
      <div className="bg-white border-b border-slate-100 px-8 py-5 flex items-center justify-between flex-shrink-0">
        <div>
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Vendor Onboarding</p>
          <h2 className="font-black text-slate-900 text-lg mt-0.5">{vendorName}</h2>
        </div>
        {sessionId && (
          <div className="text-right">
            <p className="text-[10px] font-black text-slate-300 uppercase tracking-widest">Session</p>
            <p className="font-mono text-xs text-slate-400 mt-0.5">{sessionId}</p>
          </div>
        )}
      </div>

      {/* Step tracker */}
      <div className="bg-white border-b border-slate-100 px-8 pt-6 pb-4 flex-shrink-0">
        <StepTracker
          steps={STEPS}
          currentIndex={stepIndex}
          phase={phase}
          completedKeys={completedKeys}
        />
      </div>

      {/* Main content */}
      <div className="flex-1 overflow-hidden px-8 py-6">
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

      {/* Live audit strip */}
      <AuditStrip logs={auditLog} />
    </div>
  );
}
