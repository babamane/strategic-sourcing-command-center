"""SQLAlchemy ORM models — compatible with SQLite (dev) and PostgreSQL (prod)."""
from sqlalchemy import (
    Column, String, Float, Boolean, DateTime, Text, Integer,
    ForeignKey, JSON, create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from backend.config import DATABASE_URL

Base = declarative_base()

# SQLite needs check_same_thread=False; PostgreSQL doesn't accept that kwarg
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine       = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Tables ────────────────────────────────────────────────────────────────────

class VendorOnboardingSession(Base):
    """Master session row — one per vendor onboarding run."""
    __tablename__ = "vendor_onboarding_sessions"

    id            = Column(String(16), primary_key=True)
    vendor_name   = Column(String(255), nullable=False, index=True)
    # Status mirrors the LangGraph node names + terminal states
    status        = Column(String(64), default="discovery")   # discovery | qualification_hitl | risk_audit | contract_hitl | decision | approved | rejected
    current_stage = Column(String(64), default="discovery")
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    hitl_overrides = Column(JSON, nullable=True)   # user's manual field overrides
    final_verdict  = Column(String(32), nullable=True)   # GO | CONDITIONAL_GO | NO_GO


class DiscoveryLog(Base):
    """Stage 1 — Supplier Discovery."""
    __tablename__ = "discovery_logs"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    session_id      = Column(String(16), ForeignKey("vendor_onboarding_sessions.id"), nullable=False, index=True)
    vendor_name     = Column(String(255))
    company_summary = Column(Text)
    founded         = Column(String(32))
    headquarters    = Column(String(255))
    employees       = Column(String(64))
    products        = Column(JSON)
    market_segment  = Column(String(255))
    recent_funding  = Column(Text)
    market_position = Column(Text)
    sources         = Column(JSON)          # Tavily URLs
    created_at      = Column(DateTime, default=datetime.utcnow)


class ComplianceVerification(Base):
    """Stage 2 — Qualification / Compliance (HITL gate)."""
    __tablename__ = "compliance_verifications"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    session_id       = Column(String(16), ForeignKey("vendor_onboarding_sessions.id"), nullable=False, index=True)
    soc2_status      = Column(String(128))
    iso27001         = Column(String(128))
    gdpr_compliant   = Column(Boolean)
    esg_grade        = Column(String(4))
    certifications   = Column(JSON)
    compliance_notes = Column(Text)
    hitl_approved    = Column(Boolean, nullable=True)    # None = pending
    hitl_notes       = Column(Text, nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)


class RiskScore(Base):
    """Stage 3 — Automated Risk Audit."""
    __tablename__ = "risk_scores"

    id                   = Column(Integer, primary_key=True, autoincrement=True)
    session_id           = Column(String(16), ForeignKey("vendor_onboarding_sessions.id"), nullable=False, index=True)
    score                = Column(Float)
    level                = Column(String(16))   # LOW | MEDIUM | HIGH
    security_rating      = Column(String(4))
    financial_stability  = Column(String(64))
    risk_factors         = Column(JSON)
    cyber_monitoring     = Column(JSON)
    financial_monitoring = Column(JSON)
    recommendation       = Column(Text)
    created_at           = Column(DateTime, default=datetime.utcnow)


class ContractReview(Base):
    """Stage 4 — Contract Review (HITL gate)."""
    __tablename__ = "contract_reviews"

    id                    = Column(Integer, primary_key=True, autoincrement=True)
    session_id            = Column(String(16), ForeignKey("vendor_onboarding_sessions.id"), nullable=False, index=True)
    suggested_term        = Column(String(64))
    payment_terms         = Column(String(64))
    sla_uptime            = Column(String(32))
    termination_notice    = Column(String(64))
    key_clauses           = Column(JSON)
    negotiation_blueprint = Column(JSON)
    price_protection      = Column(Text)
    msa_status            = Column(String(128))
    savings_opportunity   = Column(String(128))
    hitl_approved         = Column(Boolean, nullable=True)
    hitl_notes            = Column(Text, nullable=True)
    created_at            = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    """Immutable audit trail — every state change and user action."""
    __tablename__ = "audit_logs"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(16), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)   # WORKFLOW_STARTED | DATA_FETCHED | USER_CONTINUED | USER_CANCELLED
    step       = Column(String(64), nullable=True)    # discovery | qualification | risk | contract | decision
    timestamp  = Column(DateTime, default=datetime.utcnow)
    extra      = Column(JSON, nullable=True)          # arbitrary context dict


class ProductionVendor(Base):
    """Final table — vendors move here after GO verdict (Mission Accomplished)."""
    __tablename__ = "production_vendors"

    id              = Column(String(16), primary_key=True)
    session_id      = Column(String(16), ForeignKey("vendor_onboarding_sessions.id"), nullable=False)
    vendor_name     = Column(String(255), nullable=False, index=True)
    onboarded_at    = Column(DateTime, default=datetime.utcnow)
    verdict_summary = Column(Text)
    total_savings   = Column(String(128))
    risk_level      = Column(String(16))
    esg_grade       = Column(String(4))
    contract_term   = Column(String(64))
    sla_uptime      = Column(String(32))
