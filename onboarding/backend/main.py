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
