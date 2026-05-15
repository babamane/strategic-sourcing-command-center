"""All database read/write operations — keeps main.py clean."""
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from backend.db.models import (
    VendorOnboardingSession, DiscoveryLog, ComplianceVerification,
    RiskScore, ContractReview, ProductionVendor, AuditLog,
)
from backend.schemas import (
    DiscoveryResult, QualificationResult, RiskResult, ContractResult, VerdictResult,
)


def _new_id() -> str:
    return str(uuid.uuid4())[:12]


# ── Session ───────────────────────────────────────────────────────────────────

def create_session(db: Session, vendor_name: str) -> VendorOnboardingSession:
    s = VendorOnboardingSession(id=_new_id(), vendor_name=vendor_name)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def get_session(db: Session, session_id: str) -> VendorOnboardingSession | None:
    return db.query(VendorOnboardingSession).filter_by(id=session_id).first()


def list_sessions(db: Session) -> list[VendorOnboardingSession]:
    return db.query(VendorOnboardingSession).order_by(
        VendorOnboardingSession.created_at.desc()
    ).all()


def update_session_status(db: Session, session_id: str, status: str, stage: str):
    s = get_session(db, session_id)
    if s:
        s.status        = status
        s.current_stage = stage
        s.updated_at    = datetime.utcnow()
        db.commit()


def set_session_overrides(db: Session, session_id: str, overrides: dict):
    s = get_session(db, session_id)
    if s:
        existing = s.hitl_overrides or {}
        existing.update(overrides)
        s.hitl_overrides = existing
        s.updated_at = datetime.utcnow()
        db.commit()


# ── Stage logs ────────────────────────────────────────────────────────────────

def log_discovery(db: Session, session_id: str, r: DiscoveryResult) -> DiscoveryLog:
    row = DiscoveryLog(
        session_id      = session_id,
        vendor_name     = r.company_summary[:80],
        company_summary = r.company_summary,
        founded         = r.founded,
        headquarters    = r.headquarters,
        employees       = r.employees,
        products        = r.products,
        market_segment  = r.market_segment,
        recent_funding  = r.recent_funding,
        market_position = r.market_position,
        sources         = r.sources,
    )
    db.add(row)
    db.commit()
    return row


def log_qualification(db: Session, session_id: str, r: QualificationResult) -> ComplianceVerification:
    row = ComplianceVerification(
        session_id       = session_id,
        soc2_status      = r.soc2_status,
        iso27001         = r.iso27001,
        gdpr_compliant   = r.gdpr_compliant,
        esg_grade        = r.esg_grade,
        certifications   = r.certifications,
        compliance_notes = r.compliance_notes,
    )
    db.add(row)
    db.commit()
    return row


def approve_qualification(db: Session, session_id: str, approved: bool, notes: str = ""):
    row = db.query(ComplianceVerification).filter_by(session_id=session_id).order_by(
        ComplianceVerification.id.desc()
    ).first()
    if row:
        row.hitl_approved = approved
        row.hitl_notes    = notes
        db.commit()


def log_risk(db: Session, session_id: str, r: RiskResult) -> RiskScore:
    row = RiskScore(
        session_id           = session_id,
        score                = r.score,
        level                = r.level,
        security_rating      = r.security_rating,
        financial_stability  = r.financial_stability,
        risk_factors         = r.risk_factors,
        cyber_monitoring     = r.cyber_monitoring,
        financial_monitoring = r.financial_monitoring,
        recommendation       = r.recommendation,
    )
    db.add(row)
    db.commit()
    return row


def log_contract(db: Session, session_id: str, r: ContractResult) -> ContractReview:
    row = ContractReview(
        session_id            = session_id,
        suggested_term        = r.suggested_term,
        payment_terms         = r.payment_terms,
        sla_uptime            = r.sla_uptime,
        termination_notice    = r.termination_notice,
        key_clauses           = r.key_clauses,
        negotiation_blueprint = [p.model_dump() for p in r.negotiation_blueprint],
        price_protection      = r.price_protection,
        msa_status            = r.msa_status,
        savings_opportunity   = r.savings_opportunity,
    )
    db.add(row)
    db.commit()
    return row


def approve_contract(db: Session, session_id: str, approved: bool, notes: str = ""):
    row = db.query(ContractReview).filter_by(session_id=session_id).order_by(
        ContractReview.id.desc()
    ).first()
    if row:
        row.hitl_approved = approved
        row.hitl_notes    = notes
        db.commit()


# ── Production vendor (Mission Accomplished) ──────────────────────────────────

def promote_to_production(db: Session, session_id: str, verdict: VerdictResult):
    session = get_session(db, session_id)
    risk    = db.query(RiskScore).filter_by(session_id=session_id).order_by(RiskScore.id.desc()).first()
    qual    = db.query(ComplianceVerification).filter_by(session_id=session_id).order_by(ComplianceVerification.id.desc()).first()
    contract= db.query(ContractReview).filter_by(session_id=session_id).order_by(ContractReview.id.desc()).first()

    pv = ProductionVendor(
        id              = _new_id(),
        session_id      = session_id,
        vendor_name     = session.vendor_name if session else "Unknown",
        verdict_summary = verdict.summary,
        total_savings   = verdict.total_savings,
        risk_level      = risk.level if risk else "UNKNOWN",
        esg_grade       = qual.esg_grade if qual else "B",
        contract_term   = contract.suggested_term if contract else "TBD",
        sla_uptime      = contract.sla_uptime if contract else "TBD",
    )
    db.add(pv)
    if session:
        session.final_verdict = verdict.verdict
        session.status        = "approved"
        session.current_stage = "approved"
        session.updated_at    = datetime.utcnow()
    db.commit()
    return pv


def add_audit_log(db: Session, session_id: str, event_type: str, step: str = None, extra: dict = None):
    row = AuditLog(session_id=session_id, event_type=event_type, step=step, extra=extra or {})
    db.add(row)
    db.commit()


def get_audit_logs(db: Session, session_id: str) -> list[AuditLog]:
    return db.query(AuditLog).filter_by(session_id=session_id).order_by(AuditLog.timestamp).all()


def get_production_vendors(db: Session) -> list[ProductionVendor]:
    return db.query(ProductionVendor).order_by(ProductionVendor.onboarded_at.desc()).all()


# ── Snapshot helper (assembles full session dict for API) ─────────────────────

def session_snapshot(db: Session, session_id: str) -> dict | None:
    s = get_session(db, session_id)
    if not s:
        return None

    disc  = db.query(DiscoveryLog).filter_by(session_id=session_id).order_by(DiscoveryLog.id.desc()).first()
    qual  = db.query(ComplianceVerification).filter_by(session_id=session_id).order_by(ComplianceVerification.id.desc()).first()
    risk  = db.query(RiskScore).filter_by(session_id=session_id).order_by(RiskScore.id.desc()).first()
    contr = db.query(ContractReview).filter_by(session_id=session_id).order_by(ContractReview.id.desc()).first()

    def _row(obj, exclude=("id", "session_id", "created_at")):
        if obj is None:
            return None
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_") and k not in exclude}

    # Build a lightweight verdict summary from stage data so the UI has a single
    # object to read without running the full decision agent again.
    verdict_obj = None
    if s.final_verdict and risk and qual and contr:
        verdict_obj = {
            "verdict":            s.final_verdict,
            "summary":            (
                f"Risk Score {risk.score}/10 ({risk.level}). "
                f"SOC2: {qual.soc2_status}. ESG: {qual.esg_grade}. "
                f"GDPR: {'Compliant' if qual.gdpr_compliant else 'Non-Compliant'}. "
                f"Savings: {contr.savings_opportunity}."
            ),
            "aggregated_logic":   (
                f"SOC2: {qual.soc2_status} | ESG: {qual.esg_grade} | "
                f"Risk: {risk.score}/10 ({risk.level}) | "
                f"Security: {risk.security_rating}"
            ),
            "total_savings":      contr.savings_opportunity,
            "risk_summary":       f"Score {risk.score}/10 ({risk.level}) — {risk.security_rating}",
            "compliance_summary": (
                f"SOC2: {qual.soc2_status} | ISO 27001: {qual.iso27001} | "
                f"ESG: {qual.esg_grade}"
            ),
        }

    return {
        "id":            s.id,
        "vendor_name":   s.vendor_name,
        "status":        s.status,
        "current_stage": s.current_stage,
        "created_at":    s.created_at.isoformat(),
        "hitl_overrides": s.hitl_overrides,
        "final_verdict": s.final_verdict,
        "discovery":     _row(disc),
        "qualification": _row(qual),
        "risk":          _row(risk),
        "contract":      _row(contr),
        "verdict":       verdict_obj,
    }
