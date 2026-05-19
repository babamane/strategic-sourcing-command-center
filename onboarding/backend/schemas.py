"""Pydantic models — every LLM response is validated through these before touching the DB or UI."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ── Per-stage LLM output models ───────────────────────────────────────────────

class DiscoveryResult(BaseModel):
    # Core
    company_summary:      str       = Field(description="3-4 sentence company overview")
    founded:              str       = Field(default="Unknown")
    headquarters:         str       = Field(default="Unknown")
    employees:            str       = Field(default="Unknown")
    market_segment:       str       = Field(default="Enterprise")
    recent_funding:       str       = Field(default="Unknown")
    market_position:      str       = Field(default="Unknown")
    sources:              List[str] = Field(default_factory=list)
    # Detailed
    revenue_estimate:     str       = Field(default="Unknown")
    products:             List[str] = Field(default_factory=list)
    product_descriptions: Dict[str, str] = Field(default_factory=dict, description="product name -> description")
    tech_stack:           List[str] = Field(default_factory=list)
    key_executives:       List[str] = Field(default_factory=list, description="Name — Title")
    main_competitors:     List[str] = Field(default_factory=list)
    customer_segments:    List[str] = Field(default_factory=list)
    geographic_presence:  List[str] = Field(default_factory=list)
    recent_news:          List[str] = Field(default_factory=list, description="recent developments, max 4")
    analyst_rating:       str       = Field(default="Not Rated")
    business_model:       str       = Field(default="SaaS subscription")
    growth_rate:          str       = Field(default="Unknown")


class QualificationResult(BaseModel):
    # Core
    soc2_status:       str       = Field(default="Unknown")
    iso27001:          str       = Field(default="Unknown")
    gdpr_compliant:    bool      = Field(default=True)
    esg_grade:         str       = Field(default="B")
    certifications:    List[str] = Field(default_factory=list)
    compliance_notes:  str       = Field(default="")
    # Detailed
    soc2_scope:        str       = Field(default="Unknown", description="Systems and services in scope")
    last_audit_date:   str       = Field(default="Unknown")
    next_audit_date:   str       = Field(default="Unknown")
    sub_processors:    List[str] = Field(default_factory=list, description="Key sub-processors / cloud providers")
    data_residency:    str       = Field(default="Unknown", description="Where customer data is stored")
    pentest_status:    str       = Field(default="Unknown", description="Penetration testing cadence and last date")
    hipaa_compliant:   bool      = Field(default=False)
    ccpa_compliant:    bool      = Field(default=True)
    pci_dss:           str       = Field(default="Not Applicable")
    esg_environmental: str       = Field(default="B", description="Environmental pillar grade")
    esg_social:        str       = Field(default="B", description="Social pillar grade")
    esg_governance:    str       = Field(default="A", description="Governance pillar grade")
    audit_findings:    str       = Field(default="No material findings")
    remediation_status: str      = Field(default="N/A")
    bug_bounty:        str       = Field(default="Unknown")
    sources:           List[str] = Field(default_factory=list)


class RiskResult(BaseModel):
    # Core
    score:                float          = Field(ge=1.0, le=10.0)
    level:                str            = Field(description="LOW / MEDIUM / HIGH")
    security_rating:      str            = Field(default="B")
    financial_stability:  str            = Field(default="Stable")
    risk_factors:         List[str]      = Field(default_factory=list)
    cyber_monitoring:     Dict[str, Any] = Field(default_factory=dict)
    financial_monitoring: Dict[str, Any] = Field(default_factory=dict)
    recommendation:       str            = Field(default="")
    # Detailed
    financial_risk_score:    float       = Field(default=3.0, ge=1.0, le=10.0)
    cyber_risk_score:        float       = Field(default=3.0, ge=1.0, le=10.0)
    operational_risk_score:  float       = Field(default=3.0, ge=1.0, le=10.0)
    credit_rating:           str         = Field(default="Unknown")
    revenue_trend:           str         = Field(default="Stable")
    revenue_growth_yoy:      str         = Field(default="Unknown")
    debt_ratio:              str         = Field(default="Unknown")
    cash_position:           str         = Field(default="Unknown")
    cve_history:             str         = Field(default="No critical CVEs in past 12 months")
    patch_cadence:           str         = Field(default="Unknown")
    incident_history:        List[str]   = Field(default_factory=list)
    regulatory_risk:         str         = Field(default="Low")
    key_person_risk:         str         = Field(default="Low")
    geographic_concentration: str        = Field(default="Diversified")
    supply_chain_risk:       str         = Field(default="Low")
    risk_mitigation:         List[str]   = Field(default_factory=list)
    industry_benchmark:      str         = Field(default="In line with industry peers")
    sources:                 List[str]   = Field(default_factory=list)


class NegotiationPoint(BaseModel):
    clause:       str
    current:      str
    target:       str
    rationale:    str
    priority:     str = Field(default="Medium", description="High / Medium / Low")
    talking_point: str = Field(default="")


class ContractResult(BaseModel):
    # Core
    suggested_term:        str                    = Field(default="24 months")
    payment_terms:         str                    = Field(default="Net 30")
    sla_uptime:            str                    = Field(default="99.9%")
    termination_notice:    str                    = Field(default="60 days")
    key_clauses:           List[str]              = Field(default_factory=list)
    negotiation_blueprint: List[NegotiationPoint] = Field(default_factory=list)
    price_protection:      str                    = Field(default="")
    msa_status:            str                    = Field(default="Draft")
    savings_opportunity:   str                    = Field(default="TBD")
    # Detailed
    liability_cap:         str       = Field(default="12 months of paid fees")
    ip_ownership:          str       = Field(default="Customer retains all output data and derived works")
    auto_renewal_terms:    str       = Field(default="Auto-renews with 90-day opt-out window")
    data_portability:      str       = Field(default="30-day export window on termination")
    governing_law:         str       = Field(default="State of California, USA")
    dispute_resolution:    str       = Field(default="Binding arbitration, AAA rules")
    audit_rights:          str       = Field(default="Customer may audit annually with 30 days notice")
    exit_assistance:       str       = Field(default="60-day transition assistance included")
    sla_response_time:     str       = Field(default="P1: 1hr, P2: 4hr, P3: 24hr")
    sla_credits:           str       = Field(default="5% of monthly fee per 0.1% below SLA")
    subcontractor_rights:  str       = Field(default="Vendor must disclose and seek approval for sub-processors")
    savings_breakdown:     List[str] = Field(default_factory=list, description="Line items of savings")
    sources:               List[str] = Field(default_factory=list)


class VerdictResult(BaseModel):
    # Core
    verdict:            str       = Field(description="GO / CONDITIONAL_GO / NO_GO")
    color:              str       = Field(description="green / orange / red")
    summary:            str
    aggregated_logic:   str
    total_savings:      str       = Field(default="TBD")
    risk_summary:       str       = Field(default="")
    compliance_summary: str       = Field(default="")
    # Detailed
    scorecard:          List[Dict[str, str]] = Field(default_factory=list, description="[{criterion, status, detail}]")
    conditions:         List[str]  = Field(default_factory=list, description="Conditions if CONDITIONAL_GO")
    next_steps:         List[str]  = Field(default_factory=list, description="Required actions post-approval")
    onboarding_timeline: str       = Field(default="4-6 weeks")
    required_approvals: List[str]  = Field(default_factory=list)
    integration_notes:  str        = Field(default="")
    review_checkpoint:  str        = Field(default="90-day review post go-live")


# ── API request / response models ─────────────────────────────────────────────

class StartOnboardingRequest(BaseModel):
    vendor_name: str


class HITLDecisionRequest(BaseModel):
    decision:   str            = Field(description="approve or modify")
    notes:      Optional[str]  = ""
    overrides:  Optional[Dict[str, Any]] = None


class SessionOut(BaseModel):
    id:            str
    vendor_name:   str
    status:        str
    current_stage: str
    created_at:    str
    discovery:     Optional[Dict[str, Any]] = None
    qualification: Optional[Dict[str, Any]] = None
    risk:          Optional[Dict[str, Any]] = None
    contract:      Optional[Dict[str, Any]] = None
    verdict:       Optional[Dict[str, Any]] = None
    hitl_overrides: Optional[Dict[str, Any]] = None
