"""
adk_agent.py  —  VendorFlow AI · Contract Intelligence Agent
=============================================================
Two operating modes:
  Full mode   — google-adk + Ollama running → real LLM reasoning
  Simulation  — ADK missing / Ollama offline → tools run directly, no LLM

The rest of the CRA system always works in either mode.
"""

import os
import re
import asyncio
import urllib.request
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
# SAFE ADK IMPORT  — never crashes even when package is missing
# ──────────────────────────────────────────────────────────────────────────────
ADK_AVAILABLE = False

try:
    from google.adk.agents import Agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.adk.tools import FunctionTool
    from google.genai import types as genai_types
    ADK_AVAILABLE = True
    print("[ADK] google-adk loaded — Full AI mode available")
except ImportError:
    # Stub classes so nothing else in this file raises NameError
    class Agent:
        def __init__(self, **kw): pass
    class Runner:
        def __init__(self, **kw): pass
    class InMemorySessionService:
        async def create_session(self, **kw):
            return type("S", (), {"id": "sim"})()
    class FunctionTool:
        def __init__(self, func=None, **kw): self.func = func
    class genai_types:
        class Content:
            def __init__(self, **kw): pass
        class Part:
            def __init__(self, **kw): pass
    print("[ADK] google-adk not installed — Simulation mode active")
    print("[ADK] To enable Full AI: pip install google-adk litellm")

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────────────
DATA_DIR        = os.getenv("DATA_DIR",        "data")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL",    "orieg/gemma3-tools:12b-ft")

MAX_SAME_TOOL_CALLS  = 2
MAX_TOTAL_TOOL_CALLS = 12

TOOL_SEQUENCE = [
    "parse_alert",
    "fetch_contracts",
    "calculate_sentiment",
    "generate_docx_report",
]

# ──────────────────────────────────────────────────────────────────────────────
# VENDOR MAPPING
# ──────────────────────────────────────────────────────────────────────────────
VENDORS = ["Atlassify","Nexaflow","Veloxa","Prismly","Cloudora","Databridge"]

def _map_vendor(contract_id: str) -> str:
    digits = "".join(ch for ch in str(contract_id) if ch.isdigit())
    try:    idx = int(digits) if digits else 0
    except: idx = 0
    return VENDORS[idx % len(VENDORS)]

# ──────────────────────────────────────────────────────────────────────────────
# CONTRACT STORE
# ──────────────────────────────────────────────────────────────────────────────
CONTRACT_STORE = {
    "C-1064": {
        "id":"C-1064","reference":"PSA-2024-V2L2-001",
        "vendor":_map_vendor("C-1064"),"license":"Contributor",
        "owner":"IT","criticality":"Medium","stage":"Approval",
        "start_date":"2023-11-29","end_date":"2026-05-14",
        "renewal_month":"June 2026","days_to_renewal":180,
        "total_users":2457,"active_users":1815,"avg_utilization_pct":72.9,
        "annual_budget_usd":2538,"actual_spend_usd":1968,
        "spend_pct":77.5,"budget_status":"Healthy","true_up_usd":-570,
        "doc_link":os.path.join(DATA_DIR,"contract_current_C1064.docx"),
        "prior_contract_id":"C-0821","status":"ACTIVE",
    },
    "C-0821": {
        "id":"C-0821","reference":"PSA-2021-V2L2-001",
        "vendor":_map_vendor("C-0821"),"license":"Contributor",
        "owner":"IT","criticality":"Low","stage":"Closed / Executed",
        "start_date":"2020-12-01","end_date":"2023-11-30",
        "renewal_month":"N/A","days_to_renewal":0,
        "total_users":1800,"active_users":1170,"avg_utilization_pct":65.0,
        "annual_budget_usd":1950,"actual_spend_usd":1430,
        "spend_pct":73.3,"budget_status":"Healthy","true_up_usd":-520,
        "doc_link":os.path.join(DATA_DIR,"contract_prior_C0821.docx"),
        "prior_contract_id":None,"status":"EXPIRED",
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# OLLAMA CHECK
# ──────────────────────────────────────────────────────────────────────────────
def _ollama_is_running() -> bool:
    try:
        req = urllib.request.Request(
            f"{OLLAMA_BASE_URL}/api/tags",
            headers={"User-Agent":"vendorflow-cra/1.0"},
        )
        with urllib.request.urlopen(req, timeout=3) as r:
            return r.status == 200
    except Exception:
        return False

def check_connection() -> bool:
    if _ollama_is_running():
        print(f"[LLM] Ollama reachable -> model: {OLLAMA_MODEL}")
        return True
    print(f"[LLM] Ollama NOT reachable at {OLLAMA_BASE_URL} -> Simulation mode")
    return False

def _resolve_model():
    if not ADK_AVAILABLE:
        return None, "simulated"
    if _ollama_is_running():
        try:
            from google.adk.models.lite_llm import LiteLlm
            return LiteLlm(model=f"ollama/{OLLAMA_MODEL}"), "ollama"
        except Exception as e:
            print(f"[LLM] LiteLlm init failed: {e}")
    return None, "simulated"

# ──────────────────────────────────────────────────────────────────────────────
# TOOLS
# ──────────────────────────────────────────────────────────────────────────────
def parse_alert(alert_text: str) -> dict:
    """Parse renewal alert and extract contract metadata."""
    print(f"\n[TOOL] parse_alert <- {len(alert_text)} chars")
    contract_id = "C-1064"
    m = re.search(r"C-\d{4}", alert_text, re.IGNORECASE)
    if m:
        contract_id = m.group(0).upper()
    days = 180
    dm = re.search(r"(\d+)\s*day", alert_text, re.IGNORECASE)
    if dm:
        try: days = int(dm.group(1))
        except: pass
    result = {
        "contract_id": contract_id,
        "vendor": _map_vendor(contract_id),
        "license_type": "Contributor",
        "avg_utilization_pct": 73.9,
        "days_remaining": days,
        "renewal_month": "June 2026",
        "raw_alert": alert_text[:500],
        "parsed_at": datetime.utcnow().isoformat(),
    }
    print(f"[TOOL] parse_alert -> contract_id={contract_id}, days={days}")
    return result


def fetch_contracts(contract_id: str) -> dict:
    """Fetch current and prior contract records."""
    print(f"\n[TOOL] fetch_contracts <- contract_id={contract_id}")
    current = CONTRACT_STORE.get(contract_id) or {
        "id": contract_id, "vendor": _map_vendor(contract_id),
        "license": "Full", "owner": "IT", "criticality": "Medium",
        "stage": "Planning", "days_to_renewal": 180,
        "annual_budget_usd": 5000, "actual_spend_usd": 4200,
        "avg_utilization_pct": 74.0, "budget_status": "Healthy",
        "prior_contract_id": None, "status": "ACTIVE",
        "total_users": 100, "active_users": 74,
    }
    prior_id = current.get("prior_contract_id")
    prior    = CONTRACT_STORE.get(prior_id) if prior_id else None
    print(f"[TOOL] fetch_contracts -> current={current['id']}, prior={prior['id'] if prior else 'None'}")
    return {"current": current, "prior": prior}


def calculate_sentiment(current: dict, prior: dict | None) -> dict:
    """Score contract health based on utilization, spend and urgency."""
    print(f"\n[TOOL] calculate_sentiment <- vendor={current.get('vendor','?')}")
    score = 70
    flags = []
    trend = {}

    util  = float(current.get("avg_utilization_pct", 70))
    spend = float(current.get("actual_spend_usd", 0))
    budg  = float(current.get("annual_budget_usd", 1)) or 1
    days  = int(  current.get("days_to_renewal",   90))

    if util >= 85:
        score += 15; flags.append("High utilization — full license usage")
    elif util >= 70:
        score += 5;  flags.append("Good utilization — within healthy range")
    else:
        score -= 15; flags.append("Low utilization (<70%) — consider right-sizing")

    ratio = spend / budg
    if ratio > 1.05:
        score -= 10; flags.append("Spend exceeds budget — review overages")
    elif ratio < 0.85:
        score += 5;  flags.append("Spend well within budget")

    if days <= 30:
        score -= 20; flags.append("CRITICAL — <=30 days to renewal")
    elif days <= 90:
        score -= 8;  flags.append("Escalation — <=90 days to renewal")

    if prior:
        prior_util = float(prior.get("avg_utilization_pct", util))
        delta = round(util - prior_util, 1)
        trend = {"utilization_delta": delta,
                 "direction": "up" if delta >= 0 else "down",
                 "prior_contract": prior.get("id","N/A")}
        if delta > 5:
            score += 5; flags.append(f"Utilization improved +{delta}% vs prior")
        elif delta < -5:
            score -= 5; flags.append(f"Utilization declined {delta}% vs prior")

    score = max(0, min(100, score))
    if score >= 80:
        label, color = "Healthy", "#10B981"
    elif score >= 60:
        label, color = "Average", "#F59E0B"
    else:
        label, color = "At Risk", "#EF4444"

    print(f"[TOOL] calculate_sentiment -> score={score}, label={label}")
    return {"score":score,"label":label,"color":color,"flags":flags,"trend":trend,
            "computed_at":datetime.utcnow().isoformat()}


def generate_docx_report(alert_data: dict, contracts: dict, sentiment: dict) -> str:
    """Generate a DOCX/TXT renewal summary report and return the file path."""
    print(f"\n[TOOL] generate_docx_report <- generating report ...")
    cid     = alert_data.get("contract_id","unknown")
    current = contracts.get("current", {})
    vendor  = current.get("vendor", _map_vendor(cid))

    draft_dir = os.path.join(DATA_DIR, "renewal_drafts")
    os.makedirs(draft_dir, exist_ok=True)

    # Try python-docx first (it IS installed in requirements.txt)
    try:
        from docx import Document
        doc = Document()
        doc.add_heading("VendorFlow AI — Contract Renewal Summary", 0)
        doc.add_heading(f"Contract: {cid}  |  Vendor: {vendor}", 1)
        doc.add_paragraph(f"Generated     : {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        doc.add_paragraph(f"Stage         : {current.get('stage','Planning')}")
        doc.add_paragraph(f"Days Remaining: {current.get('days_to_renewal','N/A')}")
        doc.add_heading("Utilization", 2)
        doc.add_paragraph(
            f"Active Users : {current.get('active_users','N/A')} / {current.get('total_users','N/A')}\n"
            f"Avg Util %   : {current.get('avg_utilization_pct','N/A')}%"
        )
        doc.add_heading("Budget", 2)
        doc.add_paragraph(
            f"Annual Budget: ${float(current.get('annual_budget_usd',0)):,.2f}\n"
            f"Actual Spend : ${float(current.get('actual_spend_usd', 0)):,.2f}\n"
            f"Status       : {current.get('budget_status','N/A')}"
        )
        doc.add_heading("Sentiment", 2)
        doc.add_paragraph(
            f"Score : {sentiment.get('score','N/A')}/100\n"
            f"Label : {sentiment.get('label','N/A')}\n"
            f"Flags : {'; '.join(sentiment.get('flags',[]))}"
        )
        out = os.path.join(draft_dir, f"summary_report_{cid}.docx")
        doc.save(out)
        print(f"[TOOL] generate_docx_report -> {out}")
        return out
    except Exception as e:
        print(f"[TOOL] python-docx unavailable ({e}) — writing plain-text")

    # Plain-text fallback
    out = os.path.join(draft_dir, f"summary_report_{cid}.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join([
            "=== VENDORFLOW AI — CONTRACT RENEWAL SUMMARY ===",
            f"Contract      : {cid}",
            f"Vendor        : {vendor}",
            f"Generated     : {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            f"Stage         : {current.get('stage','N/A')}",
            f"Days Remaining: {current.get('days_to_renewal','N/A')}",
            "",
            "--- UTILIZATION ---",
            f"Active Users  : {current.get('active_users','N/A')} / {current.get('total_users','N/A')}",
            f"Utilization % : {current.get('avg_utilization_pct','N/A')}%",
            "",
            "--- BUDGET ---",
            f"Annual Budget : ${float(current.get('annual_budget_usd',0)):,.2f}",
            f"Actual Spend  : ${float(current.get('actual_spend_usd', 0)):,.2f}",
            f"Status        : {current.get('budget_status','N/A')}",
            "",
            "--- SENTIMENT ---",
            f"Score         : {sentiment.get('score','N/A')}/100",
            f"Label         : {sentiment.get('label','N/A')}",
            f"Flags         : {'; '.join(sentiment.get('flags',[]))}",
            "",
            "=== END ===",
        ]))
    print(f"[TOOL] generate_docx_report -> {out}")
    return out

# ──────────────────────────────────────────────────────────────────────────────
# SIMULATION RUNNER
# ──────────────────────────────────────────────────────────────────────────────
def _run_simulation(alert_text: str) -> bool:
    print("\n[AGENT] Simulation mode — running tools directly")
    alert_data  = parse_alert(alert_text)
    contracts   = fetch_contracts(alert_data["contract_id"])
    sentiment   = calculate_sentiment(contracts.get("current",{}), contracts.get("prior"))
    report_path = generate_docx_report(alert_data, contracts, sentiment)
    print(f"\n[AGENT] Simulation complete -> {report_path}")
    return True

# ──────────────────────────────────────────────────────────────────────────────
# ADK AGENT BUILD
# ──────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a Contract Intelligence Agent for VendorFlow AI.
Call these 4 tools in EXACTLY this order:
  1. parse_alert
  2. fetch_contracts
  3. calculate_sentiment
  4. generate_docx_report
Do not skip any step. Stop after generate_docx_report succeeds."""

def build_agent():
    model, backend = _resolve_model()
    if backend == "simulated" or not ADK_AVAILABLE:
        return None, "simulated"
    try:
        agent = Agent(
            name        = "contract_renewal_agent",
            model       = model,
            instruction = SYSTEM_PROMPT,
            tools       = [
                FunctionTool(func=parse_alert),
                FunctionTool(func=fetch_contracts),
                FunctionTool(func=calculate_sentiment),
                FunctionTool(func=generate_docx_report),
            ],
        )
        return agent, backend
    except Exception as e:
        print(f"[ADK] Agent build failed: {e} — falling back to simulation")
        return None, "simulated"

# ──────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT  (called by agent_logic.py)
# ──────────────────────────────────────────────────────────────────────────────
async def run_agent(alert_text: str) -> bool:
    agent, backend = build_agent()

    if backend == "simulated":
        return _run_simulation(alert_text)

    print(f"\n[AGENT] Full ADK mode — model: {OLLAMA_MODEL}")
    try:
        session_service = InMemorySessionService()
        runner  = Runner(agent=agent, app_name="cra_app",
                         session_service=session_service)
        session = await session_service.create_session(
            app_name="cra_app", user_id="system_alert")

        msg = genai_types.Content(
            role  = "user",
            parts = [genai_types.Part(
                text = f"Process this renewal alert:\n\n{alert_text}"
            )],
        )

        tool_counts: dict = {}
        total = 0
        async for event in runner.run_async(
            user_id="system_alert", session_id=session.id, new_message=msg
        ):
            if hasattr(event, "tool_name"):
                n = event.tool_name
                tool_counts[n] = tool_counts.get(n,0) + 1
                total += 1
                if tool_counts[n] > MAX_SAME_TOOL_CALLS or total > MAX_TOTAL_TOOL_CALLS:
                    print(f"[AGENT] Loop guard triggered — stopping")
                    break
            if hasattr(event,"is_final_response") and event.is_final_response():
                print("[AGENT] ADK agent completed")
                return True
        return True
    except Exception as e:
        print(f"[AGENT] ADK error: {e} — falling back to simulation")
        return _run_simulation(alert_text)

# ──────────────────────────────────────────────────────────────────────────────
# STANDALONE TEST
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("VendorFlow AI — Contract Intelligence Agent TEST")
    print("=" * 55)
    print(f"ADK available : {ADK_AVAILABLE}")
    print(f"Ollama online : {_ollama_is_running()}")
    print()
    asyncio.run(run_agent(
        "Contract Renewal Alert\nContract ID: C-1064\n"
        "Vendor: Veloxa\nDays Remaining: 180\nOwner: IT"
    ))
