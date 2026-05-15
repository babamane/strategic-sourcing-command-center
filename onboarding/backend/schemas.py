"""Pydantic models — every LLM response is validated through these before touching the DB or UI."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ── Per-stage LLM output models ───────────────────────────────────────────────

class DiscoveryResult(BaseModel):
    company_summary:  str = Field(description="2-3 sentence company overview")
    founded:          str = Field(default="Unknown")
    headquarters:     str = Field(default="Unknown")
    employees:        str = Field(default="Unknown")
    products:         List[str] = Field(default_factory=list)
    market_segment:   str = Field(default="Enterprise")
    recent_funding:   str = Field(default="Unknown")
    market_position:  str = Field(default="Unknown")
    sources:          List[str] = Field(default_factory=list)


class QualificationResult(BaseModel):
    soc2_status:      str  = Field(default="Unknown")
    iso27001:         str  = Field(default="Unknown")
    gdpr_compliant:   bool = Field(default=True)
    esg_grade:        str  = Field(default="B", description="A / B / C / D")
    certifications:   List[str] = Field(default_factory=list)
    compliance_notes: str  = Field(default="")


class RiskResult(BaseModel):
    score:               float = Field(ge=1.0, le=10.0, description="1=lowest risk, 10=highest")
    level:               str   = Field(description="LOW / MEDIUM / HIGH")
    security_rating:     str   = Field(default="B")
    financial_stability: str   = Field(default="Stable")
    risk_factors:        List[str]        = Field(default_factory=list)
    cyber_monitoring:    Dict[str, Any]   = Field(default_factory=dict)
    financial_monitoring: Dict[str, Any]  = Field(default_factory=dict)
    recommendation:      str  = Field(default="")


class NegotiationPoint(BaseModel):
    clause:    str
    current:   str
    target:    str
    rationale: str


class ContractResult(BaseModel):
    suggested_term:       str = Field(default="24 months")
    payment_terms:        str = Field(default="Net 30")
    sla_uptime:           str = Field(default="99.9%")
    termination_notice:   str = Field(default="60 days")
    key_clauses:          List[str]              = Field(default_factory=list)
    negotiation_blueprint: List[NegotiationPoint] = Field(default_factory=list)
    price_protection:     str = Field(default="")
    msa_status:           str = Field(default="Draft")
    savings_opportunity:  str = Field(default="TBD")


class VerdictResult(BaseModel):
    verdict:             str  = Field(description="GO / CONDITIONAL_GO / NO_GO")
    color:               str  = Field(description="green / orange / red")
    summary:             str
    aggregated_logic:    str
    total_savings:       str  = Field(default="TBD")
    risk_summary:        str  = Field(default="")
    compliance_summary:  str  = Field(default="")


# ── API request / response models ─────────────────────────────────────────────

class StartOnboardingRequest(BaseModel):
    vendor_name: str


class HITLDecisionRequest(BaseModel):
    decision:   str            = Field(description="approve or modify")
    notes:      Optional[str]  = ""
    overrides:  Optional[Dict[str, Any]] = None   # field-level user overrides


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
