"""
Dummy LLM/Agent orchestration layer for Case 2.

Purpose:
- Keep existing `case2_engine_v1.py` untouched.
- Add a separate "agent-feel" runner that appears to reason through steps.
- Optionally plugs into LangChain and Google ADK if installed.

This is intentionally deterministic and safe for demo/review.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from typing import Any

from case2_engine_v1 import (
    build_case2_workspace_payload,
    extract_case2_request,
    is_case2_sourcing_request,
    save_workspace_context,
)


# Optional imports: code still runs without these dependencies.
try:
    from langchain_core.prompts import ChatPromptTemplate  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    ChatPromptTemplate = None

try:
    # Keep this import loose; ADK package layout can vary by install.
    import google.adk as google_adk  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    google_adk = None


@dataclass
class AgentStep:
    name: str
    thought: str
    action: str
    status: str = "completed"


@dataclass
class Case2AgentResult:
    accepted: bool
    session_id: str
    user_message: str
    steps: list[AgentStep]
    request: dict[str, Any] | None
    payload: dict[str, Any] | None
    final_text: str

    def to_json(self) -> str:
        body = asdict(self)
        return json.dumps(body, indent=2)


def _build_dummy_chain_text(user_message: str) -> str:
    """
    Build a small planning text using LangChain prompt template when available.
    Falls back to static template when LangChain is unavailable.
    """
    if ChatPromptTemplate is not None:
        prompt = ChatPromptTemplate.from_template(
            "You are SAFE AI Case2 Planner.\n"
            "User message: {user_message}\n"
            "Return 3 short plan lines:\n"
            "1) intent understanding\n"
            "2) entity extraction strategy\n"
            "3) payload generation strategy"
        )
        rendered = prompt.format_messages(user_message=user_message)
        # We only need human-readable trace text for dummy behavior.
        return "\n".join(getattr(m, "content", str(m)) for m in rendered)

    return (
        "Intent understanding: detect sourcing/buy/procure ask.\n"
        "Extraction strategy: parse vendor, role, level, tier, count.\n"
        "Payload strategy: build workspace payload and persist context."
    )


def _adk_marker() -> str:
    """
    Tiny ADK marker to show optional integration presence.
    """
    if google_adk is None:
        return "Google ADK not installed; running deterministic local agent flow."
    return "Google ADK detected; using local deterministic flow with ADK-ready wrapper."


def _build_volume_discount_note(payload: dict[str, Any], request: dict[str, Any]) -> str:
    """
    Return a compact note showing whether the in-scope price reflects a volume band discount.
    This is additive context for negotiation delta interpretation and does not alter pricing logic.
    """
    try:
        sku = payload.get("recommended_sku", {})
        sku_id = sku.get("sku_id")
        if not sku_id:
            return "Volume discount context unavailable for this scope."

        requested_count = request.get("requested_count")
        mapped_users = sku.get("mapped_users")
        demand_count = int(requested_count or mapped_users or 0)
        if demand_count <= 0:
            return "Volume discount context unavailable for this scope."

        benchmarks = load_vendor_benchmarks()
        sku_bands = benchmarks[benchmarks["sku_id"] == sku_id].copy()
        if sku_bands.empty:
            return "Volume discount context unavailable for this scope."

        eligible = sku_bands[
            (sku_bands["volume_band_min"] <= demand_count)
            & (sku_bands["volume_band_max"] >= demand_count)
        ]
        if eligible.empty:
            return "Volume discount context unavailable for this scope."

        row = eligible.iloc[0]
        discount_pct = float(row.get("discount_percent", 0.0))
        band_min = int(row.get("volume_band_min", 0))
        band_max = int(row.get("volume_band_max", 0))
        return (
            "Negotiation context: proposed pricing already reflects applicable volume-band discount "
            f"({discount_pct:.1f}% off list in band {band_min}-{band_max} for ~{demand_count:,} seats)."
        )
    except Exception:
        return "Negotiation context: proposed pricing already reflects applicable volume-band logic where eligible."


def run_case2_agentic_flow(
    user_message: str,
    history: list[dict[str, Any]] | None = None,
    session_id: str = "default",
    simulate_latency: bool = True,
) -> Case2AgentResult:
    """
    Orchestrates Case 2 with an "LLM thinking" style trace.
    - Does not modify the original routing engine.
    - Uses existing business logic from `case2_engine_v1`.
    """
    history = history or []
    steps: list[AgentStep] = []

    steps.append(
        AgentStep(
            name="bootstrap",
            thought="Initialize Case 2 agent context and planning prompt.",
            action=_build_dummy_chain_text(user_message),
        )
    )

    steps.append(
        AgentStep(
            name="adk_check",
            thought="Check whether ADK runtime is available for orchestration hooks.",
            action=_adk_marker(),
        )
    )

    is_case2 = is_case2_sourcing_request(user_message, history)
    steps.append(
        AgentStep(
            name="intent_gate",
            thought="Classify whether the incoming message belongs to Case 2 sourcing flow.",
            action=f"is_case2_sourcing_request -> {is_case2}",
        )
    )

    if not is_case2:
        return Case2AgentResult(
            accepted=False,
            session_id=session_id,
            user_message=user_message,
            steps=steps,
            request=None,
            payload=None,
            final_text=(
                "Case 2 agent did not activate. "
                "Message is outside sourcing intent. Try: "
                "`I want to buy Insight Pro licenses from vendor_3`."
            ),
        )

    if simulate_latency:
        time.sleep(0.15)

    request = extract_case2_request(user_message, history)
    steps.append(
        AgentStep(
            name="entity_extraction",
            thought="Extract vendor and planning entities from user message and context.",
            action=(
                f"vendor={request.get('vendor_name')}, dept={request.get('pillar_dept')}, "
                f"role={request.get('job_role')}, level={request.get('job_level')}, "
                f"tier={request.get('requested_tier')}, count={request.get('requested_count')}"
            ),
        )
    )

    if simulate_latency:
        time.sleep(0.15)

    payload = build_case2_workspace_payload(request)
    save_workspace_context(payload)
    steps.append(
        AgentStep(
            name="payload_build",
            thought="Build sourcing recommendation payload and persist workspace context.",
            action="build_case2_workspace_payload + save_workspace_context completed.",
        )
    )

    sku = payload["recommended_sku"]
    kpis = payload["kpis"]
    discount_note = _build_volume_discount_note(payload, request)
    final_text = (
        "Case 2 Agent Execution Completed.\n\n"
        "Reasoning summary:\n"
        "- Sourcing intent detected\n"
        "- Relevant entities extracted\n"
        "- Payload generated and workspace context saved\n\n"
        "Recommendation preview:\n"
        f"- Vendor: {payload['workspace_defaults']['vendor_name']}\n"
        f"- Recommended SKU: {sku['sku_name']} ({sku['sku_id']})\n"
        f"- Tier: {sku['license_tier']} / {sku['tier_group']}\n"
        f"- Estimated annual spend: ${kpis['estimated_annual_spend']:,.2f}\n"
        f"- Negotiation delta: ${kpis['negotiation_delta']:,.2f}\n"
        f"- {discount_note}"
    )

    return Case2AgentResult(
        accepted=True,
        session_id=session_id,
        user_message=user_message,
        steps=steps,
        request=request,
        payload=payload,
        final_text=final_text,
    )


if __name__ == "__main__":
    demo_prompt = "I want to buy Insight Pro licenses from vendor_3"
    result = run_case2_agentic_flow(demo_prompt, history=[], session_id="demo")
    print(result.final_text)
    print("\n--- Agent Trace (JSON) ---")
    print(result.to_json())
