"""FastAPI application — Vendor Onboarding Pipeline API.

Endpoints
─────────
POST   /sessions                        Start a new onboarding session
GET    /sessions                        List all sessions
GET    /sessions/{id}                   Full snapshot (all stage data)
POST   /sessions/{id}/approve/{stage}  HITL approve (qualification | contract)
POST   /sessions/{id}/modify/{stage}   HITL modify with field overrides
GET    /sessions/{id}/state             Raw LangGraph checkpoint state
GET    /production                      All promoted production vendors
DELETE /sessions/{id}                   Remove a session
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.config   import API_HOST, API_PORT
from backend.schemas  import StartOnboardingRequest, HITLDecisionRequest, SessionOut
from backend.db.models import SessionLocal
from backend.db import crud
from backend import workflow

app = FastAPI(title="Vendor Onboarding API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ── DB dependency ─────────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sync_graph_to_db(db: Session, session_id: str):
    """Pull the latest LangGraph checkpoint into the DB tables."""
    state = workflow.get_graph_state(session_id)
    if not state:
        return

    stage  = state.get("stage", "discovery")
    status = stage  # mirrors the stage name

    # Upsert discovery log
    if state.get("discovery"):
        from backend.schemas import DiscoveryResult
        disc = DiscoveryResult(**state["discovery"])
        crud.log_discovery(db, session_id, disc)

    # Upsert qualification
    if state.get("qualification"):
        from backend.schemas import QualificationResult
        qual = QualificationResult(**state["qualification"])
        crud.log_qualification(db, session_id, qual)

    # Upsert risk
    if state.get("risk"):
        from backend.schemas import RiskResult
        risk = RiskResult(**state["risk"])
        crud.log_risk(db, session_id, risk)

    # Upsert contract
    if state.get("contract"):
        from backend.schemas import ContractResult, NegotiationPoint
        c = state["contract"].copy()
        # Re-inflate negotiation_blueprint dicts → NegotiationPoint
        c["negotiation_blueprint"] = [
            NegotiationPoint(**item) if isinstance(item, dict) else item
            for item in c.get("negotiation_blueprint", [])
        ]
        crud.log_contract(db, session_id, ContractResult(**c))

    # If verdict reached, promote to production
    if state.get("verdict") and stage in ("approved", "rejected"):
        from backend.schemas import VerdictResult
        v = VerdictResult(**state["verdict"])
        if stage == "approved":
            crud.promote_to_production(db, session_id, v)
        else:
            s = crud.get_session(db, session_id)
            if s:
                s.status = "rejected"
                s.final_verdict = "NO_GO"
                db.commit()
        return  # status already set inside promote_to_production

    crud.update_session_status(db, session_id, status, stage)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/sessions", response_model=dict)
def create_session(req: StartOnboardingRequest, db: Session = Depends(get_db)):
    """Create session row, kick off LangGraph, run discovery, pause at qualification HITL."""
    name = req.vendor_name.strip()
    if not name:
        raise HTTPException(400, "vendor_name cannot be empty")

    session = crud.create_session(db, name)
    try:
        workflow.start_session(session.id, name)
        _sync_graph_to_db(db, session.id)
    except Exception as e:
        crud.update_session_status(db, session.id, "error", "discovery")
        raise HTTPException(500, f"Pipeline error: {e}")

    return crud.session_snapshot(db, session.id)


@app.get("/sessions", response_model=list)
def list_sessions(db: Session = Depends(get_db)):
    rows = crud.list_sessions(db)
    return [
        {"id": r.id, "vendor_name": r.vendor_name, "status": r.status,
         "current_stage": r.current_stage, "created_at": r.created_at.isoformat()}
        for r in rows
    ]


@app.get("/sessions/{session_id}", response_model=dict)
def get_session(session_id: str, db: Session = Depends(get_db)):
    snap = crud.session_snapshot(db, session_id)
    if not snap:
        raise HTTPException(404, "Session not found")
    return snap


@app.get("/sessions/{session_id}/state")
def get_raw_state(session_id: str):
    """Expose the raw LangGraph checkpoint state (debugging / UI polling)."""
    state = workflow.get_graph_state(session_id)
    if state is None:
        raise HTTPException(404, "No checkpoint found for this session")
    return state


@app.post("/sessions/{session_id}/approve/{stage}")
def approve_stage(session_id: str, stage: str, req: HITLDecisionRequest, db: Session = Depends(get_db)):
    """Human approves a HITL gate — resumes the LangGraph pipeline."""
    if stage not in ("qualification", "contract"):
        raise HTTPException(400, "stage must be 'qualification' or 'contract'")

    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    human_response = {"decision": "approve", "notes": req.notes or "", "overrides": req.overrides or {}}

    try:
        workflow.resume_session(session_id, human_response)
        _sync_graph_to_db(db, session_id)
    except Exception as e:
        raise HTTPException(500, f"Resume error: {e}")

    # Record HITL decision in DB
    if stage == "qualification":
        crud.approve_qualification(db, session_id, True, req.notes or "")
    else:
        crud.approve_contract(db, session_id, True, req.notes or "")

    return crud.session_snapshot(db, session_id)


@app.post("/sessions/{session_id}/modify/{stage}")
def modify_stage(session_id: str, stage: str, req: HITLDecisionRequest, db: Session = Depends(get_db)):
    """Human modifies data, optionally re-approves. Overrides are stored and forwarded."""
    if stage not in ("qualification", "contract"):
        raise HTTPException(400, "stage must be 'qualification' or 'contract'")

    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    # decision can be "modify" (just apply overrides, stay at HITL) or "approve" (override + proceed)
    decision = req.decision if req.decision in ("approve", "modify") else "modify"
    human_response = {
        "decision":  decision,
        "notes":     req.notes or "",
        "overrides": req.overrides or {},
    }

    crud.set_session_overrides(db, session_id, req.overrides or {})

    try:
        workflow.resume_session(session_id, human_response)
        _sync_graph_to_db(db, session_id)
    except Exception as e:
        raise HTTPException(500, f"Resume error: {e}")

    if stage == "qualification":
        crud.approve_qualification(db, session_id, decision == "approve", req.notes or "")
    else:
        crud.approve_contract(db, session_id, decision == "approve", req.notes or "")

    return crud.session_snapshot(db, session_id)


@app.post("/sessions/{session_id}/run/{step}")
def run_step(session_id: str, step: str, db: Session = Depends(get_db)):
    """Run a single pipeline step on demand and return its structured result.
    Called by the frontend wizard — one step at a time, gated by the user.
    """
    VALID = {"discovery", "qualification", "risk", "contract", "decision"}
    if step not in VALID:
        raise HTTPException(400, f"step must be one of {VALID}")

    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    vendor = session.vendor_name
    try:
        if step == "discovery":
            from backend.agents.discovery import run_discovery
            result = run_discovery(vendor)
            crud.log_discovery(db, session_id, result)
            crud.update_session_status(db, session_id, "qualification_pending", "discovery")
            crud.add_audit_log(db, session_id, "DATA_FETCHED", "discovery", {"vendor": vendor})
            return result.model_dump()

        elif step == "qualification":
            from backend.agents.qualification import run_qualification
            result = run_qualification(vendor)
            crud.log_qualification(db, session_id, result)
            crud.update_session_status(db, session_id, "risk_pending", "qualification")
            crud.add_audit_log(db, session_id, "DATA_FETCHED", "qualification")
            return result.model_dump()

        elif step == "risk":
            from backend.agents.risk import run_risk_audit
            result = run_risk_audit(vendor)
            crud.log_risk(db, session_id, result)
            crud.update_session_status(db, session_id, "contract_pending", "risk")
            crud.add_audit_log(db, session_id, "DATA_FETCHED", "risk")
            return result.model_dump()

        elif step == "contract":
            from backend.db.models import RiskScore as RiskScoreModel
            from backend.agents.contract import run_contract_review
            risk_row = db.query(RiskScoreModel).filter_by(session_id=session_id).order_by(RiskScoreModel.id.desc()).first()
            result = run_contract_review(vendor, risk_row.score if risk_row else 3.0)
            crud.log_contract(db, session_id, result)
            crud.update_session_status(db, session_id, "decision_pending", "contract")
            crud.add_audit_log(db, session_id, "DATA_FETCHED", "contract")
            return result.model_dump()

        elif step == "decision":
            from backend.db.models import (
                DiscoveryLog, ComplianceVerification,
                RiskScore as RiskScoreModel, ContractReview,
            )
            from backend.agents.decision import run_decision
            from backend.schemas import (
                DiscoveryResult, QualificationResult, RiskResult,
                ContractResult, NegotiationPoint,
            )

            d = db.query(DiscoveryLog).filter_by(session_id=session_id).order_by(DiscoveryLog.id.desc()).first()
            q = db.query(ComplianceVerification).filter_by(session_id=session_id).order_by(ComplianceVerification.id.desc()).first()
            r = db.query(RiskScoreModel).filter_by(session_id=session_id).order_by(RiskScoreModel.id.desc()).first()
            c = db.query(ContractReview).filter_by(session_id=session_id).order_by(ContractReview.id.desc()).first()

            if not all([d, q, r, c]):
                raise HTTPException(400, "Complete all prior steps before running decision")

            discovery     = DiscoveryResult(company_summary=d.company_summary, founded=d.founded, headquarters=d.headquarters, employees=d.employees, products=d.products or [], market_segment=d.market_segment, recent_funding=d.recent_funding, market_position=d.market_position, sources=d.sources or [])
            qualification = QualificationResult(soc2_status=q.soc2_status, iso27001=q.iso27001, gdpr_compliant=q.gdpr_compliant, esg_grade=q.esg_grade, certifications=q.certifications or [], compliance_notes=q.compliance_notes)
            risk          = RiskResult(score=r.score, level=r.level, security_rating=r.security_rating, financial_stability=r.financial_stability, risk_factors=r.risk_factors or [], cyber_monitoring=r.cyber_monitoring or {}, financial_monitoring=r.financial_monitoring or {}, recommendation=r.recommendation)
            bp            = [NegotiationPoint(**item) if isinstance(item, dict) else item for item in (c.negotiation_blueprint or [])]
            contract      = ContractResult(suggested_term=c.suggested_term, payment_terms=c.payment_terms, sla_uptime=c.sla_uptime, termination_notice=c.termination_notice, key_clauses=c.key_clauses or [], negotiation_blueprint=bp, price_protection=c.price_protection, msa_status=c.msa_status, savings_opportunity=c.savings_opportunity)

            verdict = run_decision(discovery, qualification, risk, contract, session.hitl_overrides or {})

            if verdict.verdict in ("GO", "CONDITIONAL_GO"):
                crud.promote_to_production(db, session_id, verdict)
            else:
                session.final_verdict = verdict.verdict
                session.status = "rejected"
                session.current_stage = "decision"
                db.commit()

            crud.add_audit_log(db, session_id, "DATA_FETCHED", "decision", {"verdict": verdict.verdict})
            return verdict.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Step error: {e}")


@app.post("/sessions/{session_id}/log")
def log_audit_event(session_id: str, body: dict, db: Session = Depends(get_db)):
    """Frontend emits audit events (USER_CONTINUED, USER_CANCELLED, etc.)."""
    crud.add_audit_log(db, session_id, body.get("event_type", "UNKNOWN"), body.get("step"), body.get("extra"))
    return {"ok": True}


@app.get("/sessions/{session_id}/audit")
def get_audit_trail(session_id: str, db: Session = Depends(get_db)):
    rows = crud.get_audit_logs(db, session_id)
    return [{"event_type": r.event_type, "step": r.step, "timestamp": r.timestamp.isoformat(), "extra": r.extra} for r in rows]


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    db.delete(session)
    db.commit()
    return {"deleted": session_id}


@app.get("/production")
def get_production_vendors(db: Session = Depends(get_db)):
    rows = crud.get_production_vendors(db)
    return [
        {
            "id":            r.id,
            "vendor_name":   r.vendor_name,
            "onboarded_at":  r.onboarded_at.isoformat(),
            "risk_level":    r.risk_level,
            "esg_grade":     r.esg_grade,
            "contract_term": r.contract_term,
            "sla_uptime":    r.sla_uptime,
            "total_savings": r.total_savings,
            "verdict_summary": r.verdict_summary,
        }
        for r in rows
    ]


if __name__ == "__main__":
    import uvicorn
    from migrations.init_db import run_migrations
    run_migrations()
    uvicorn.run("backend.main:app", host=API_HOST, port=API_PORT, reload=True)
