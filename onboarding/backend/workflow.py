"""LangGraph state machine for the vendor onboarding pipeline.

Flow:
  discovery → qualification_hitl ─(approve)→ risk_audit → contract_hitl ─(approve)→ decision → END
                                 ─(modify) ↩                             ─(modify) ↩

HITL gates pause execution by raising an Interrupt. The FastAPI layer
resumes the graph by calling graph.invoke(Command(resume=…), config=…).

Persistence: LangGraph SqliteSaver checkpoints every node's state so
the graph can be resumed after a server restart using the thread_id (= session_id).
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from typing import TypedDict, Optional, Any
from langgraph.graph  import StateGraph, END
from langgraph.types  import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from backend.schemas import (
    DiscoveryResult, QualificationResult, RiskResult, ContractResult, VerdictResult
)
from backend.agents.discovery     import run_discovery
from backend.agents.qualification import run_qualification, apply_overrides as qual_override
from backend.agents.risk          import run_risk_audit
from backend.agents.contract      import run_contract_review, apply_overrides as contract_override
from backend.agents.decision      import run_decision


# ── State schema ──────────────────────────────────────────────────────────────

class OnboardingState(TypedDict):
    session_id:    str
    vendor_name:   str
    stage:         str                     # current node name
    discovery:     Optional[dict]
    qualification: Optional[dict]
    risk:          Optional[dict]
    contract:      Optional[dict]
    verdict:       Optional[dict]
    hitl_overrides: Optional[dict]         # accumulated user modifications
    error:         Optional[str]


# ── Node implementations ───────────────────────────────────────────────────────

def node_discovery(state: OnboardingState) -> dict:
    result = run_discovery(state["vendor_name"])
    return {
        "stage":     "qualification_hitl",
        "discovery": result.model_dump(),
    }


def node_qualification(state: OnboardingState) -> dict:
    qual = run_qualification(state["vendor_name"])

    # ── HITL interrupt — pauses here until the API resumes ───────────────────
    human_response: dict = interrupt({
        "stage":   "qualification_hitl",
        "payload": qual.model_dump(),
        "message": "Review SOC2 / ESG / compliance data. Approve or modify before proceeding.",
    })

    decision  = human_response.get("decision", "approve")
    notes     = human_response.get("notes", "")
    overrides = human_response.get("overrides") or {}

    if overrides:
        qual = qual_override(qual, overrides)

    accumulated = {**(state.get("hitl_overrides") or {}), **overrides}
    if notes:
        accumulated["qualification_notes"] = notes

    return {
        "stage":          "risk_audit" if decision == "approve" else "qualification_hitl",
        "qualification":  qual.model_dump(),
        "hitl_overrides": accumulated,
    }


def node_risk_audit(state: OnboardingState) -> dict:
    risk = run_risk_audit(state["vendor_name"])
    return {
        "stage": "contract_hitl",
        "risk":  risk.model_dump(),
    }


def node_contract(state: OnboardingState) -> dict:
    risk_score = float((state.get("risk") or {}).get("score", 3.0))
    contract   = run_contract_review(state["vendor_name"], risk_score)

    # ── HITL interrupt ───────────────────────────────────────────────────────
    human_response: dict = interrupt({
        "stage":   "contract_hitl",
        "payload": contract.model_dump(),
        "message": "Review draft MSA and negotiation blueprint. Approve or modify before final decision.",
    })

    decision  = human_response.get("decision", "approve")
    notes     = human_response.get("notes", "")
    overrides = human_response.get("overrides") or {}

    if overrides:
        contract = contract_override(contract, overrides)

    accumulated = {**(state.get("hitl_overrides") or {}), **overrides}
    if notes:
        accumulated["contract_notes"] = notes

    return {
        "stage":          "decision" if decision == "approve" else "contract_hitl",
        "contract":       contract.model_dump(),
        "hitl_overrides": accumulated,
    }


def node_decision(state: OnboardingState) -> dict:
    disc  = DiscoveryResult(**state["discovery"])
    qual  = QualificationResult(**state["qualification"])
    risk  = RiskResult(**state["risk"])
    contr = ContractResult(**state["contract"])

    verdict = run_decision(disc, qual, risk, contr, state.get("hitl_overrides"))
    return {
        "stage":   "approved" if verdict.verdict != "NO_GO" else "rejected",
        "verdict": verdict.model_dump(),
    }


# ── Routing edges ─────────────────────────────────────────────────────────────

def _after_qual(state: OnboardingState) -> str:
    return state.get("stage", "qualification_hitl")


def _after_contract(state: OnboardingState) -> str:
    return state.get("stage", "contract_hitl")


def _after_decision(state: OnboardingState) -> str:
    s = state.get("stage", "approved")
    return END if s in ("approved", "rejected") else "decision"


# ── Graph assembly ────────────────────────────────────────────────────────────

def _build_graph(checkpointer):
    g = StateGraph(OnboardingState)

    g.add_node("discovery",         node_discovery)
    g.add_node("qualification_hitl", node_qualification)
    g.add_node("risk_audit",         node_risk_audit)
    g.add_node("contract_hitl",      node_contract)
    g.add_node("decision",           node_decision)

    g.set_entry_point("discovery")
    g.add_edge("discovery", "qualification_hitl")

    g.add_conditional_edges("qualification_hitl", _after_qual, {
        "risk_audit":         "risk_audit",
        "qualification_hitl": "qualification_hitl",   # re-interrupt after modify
    })

    g.add_edge("risk_audit", "contract_hitl")

    g.add_conditional_edges("contract_hitl", _after_contract, {
        "decision":      "decision",
        "contract_hitl": "contract_hitl",
    })

    g.add_conditional_edges("decision", _after_decision, {
        "approved":  END,
        "rejected":  END,
        END:         END,
    })

    return g.compile(checkpointer=checkpointer, interrupt_before=[])
    # Note: interrupts are raised INSIDE the nodes via interrupt() — not via interrupt_before


# ── Public API ────────────────────────────────────────────────────────────────

_checkpointer = MemorySaver()
graph = _build_graph(_checkpointer)


def start_session(session_id: str, vendor_name: str) -> dict:
    """Kick off the pipeline. Runs discovery then pauses at qualification HITL."""
    config = {"configurable": {"thread_id": session_id}}
    result = graph.invoke(
        {
            "session_id":    session_id,
            "vendor_name":   vendor_name,
            "stage":         "discovery",
            "discovery":     None,
            "qualification": None,
            "risk":          None,
            "contract":      None,
            "verdict":       None,
            "hitl_overrides": None,
            "error":         None,
        },
        config=config,
    )
    return result


def resume_session(session_id: str, human_response: dict) -> dict:
    """Resume after a HITL gate (qualification or contract)."""
    config = {"configurable": {"thread_id": session_id}}
    result = graph.invoke(Command(resume=human_response), config=config)
    return result


def get_graph_state(session_id: str) -> dict | None:
    """Return the latest checkpointed state for a session."""
    config = {"configurable": {"thread_id": session_id}}
    snapshot = graph.get_state(config)
    return snapshot.values if snapshot else None
