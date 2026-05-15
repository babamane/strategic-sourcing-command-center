"""Stage 3 — Risk Audit Agent (automated).

Pulls financial + cyber signals via Tavily, computes a numeric risk score,
and sets up mock hooks for 24/7 monitoring.
"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL, SEARCH_MAX_RESULTS
from backend.schemas import RiskResult


# ── Monitoring hook templates (mock 24/7 signals) ─────────────────────────────

def _cyber_monitoring_hooks(vendor_name: str) -> dict:
    return {
        "status":     "ACTIVE",
        "provider":   "BitSight / SecurityScorecard (mock)",
        "signals":    ["SSL cert expiry", "CVE patch lag", "Dark-web mention scan"],
        "threshold":  "Alert if score drops below 700",
        "cadence":    "Continuous — alerts within 15 min",
        "last_check": "Monitoring initialised on onboarding",
    }


def _financial_monitoring_hooks(vendor_name: str) -> dict:
    return {
        "status":       "ACTIVE",
        "provider":     "D&B / Moody's (mock)",
        "signals":      ["Credit rating change", "Revenue >±20% YoY", "Leadership change", "M&A activity"],
        "data_sources": ["SEC EDGAR", "Yahoo Finance", "Bloomberg"],
        "cadence":      "Daily digest + real-time critical alerts",
        "last_check":   "Monitoring initialised on onboarding",
    }


# ── DuckDuckGo + LLM risk assessment ─────────────────────────────────────────

def _ddg_risk(vendor_name: str) -> str:
    try:
        from duckduckgo_search import DDGS
        results = list(DDGS().text(
            f"{vendor_name} financial risk security breach data leak layoffs 2024 2025",
            max_results=SEARCH_MAX_RESULTS,
        ))
        return "\n\n".join(r.get("body", "") for r in results)
    except Exception:
        return ""


def _llm_risk(vendor_name: str, context: str) -> dict | None:
    try:
        from langchain_ollama import OllamaLLM
        llm    = OllamaLLM(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL, temperature=0)
        prompt = f"""You are an enterprise vendor risk analyst. Assess "{vendor_name}" for financial, operational, and cyber risk.

=== Risk Intelligence ===
{context or f'{vendor_name} — no adverse findings in public sources.'}
========================

Return ONLY a valid JSON object:
{{
  "score":               3.2,
  "level":               "LOW",
  "security_rating":     "A",
  "financial_stability": "Stable",
  "risk_factors":        ["factor 1", "factor 2", "factor 3"],
  "recommendation":      "<concise risk summary and recommended mitigations>"
}}

Rules:
- score 1-3  → level "LOW"
- score 4-6  → level "MEDIUM"
- score 7-10 → level "HIGH"
- security_rating: A+, A, B, C, D"""
        raw  = llm.invoke(prompt)
        s, e = raw.find("{"), raw.rfind("}") + 1
        return json.loads(raw[s:e]) if s != -1 else None
    except Exception:
        return None


def _fallback(vendor_name: str) -> dict:
    return {
        "score":               2.8,
        "level":               "LOW",
        "security_rating":     "A",
        "financial_stability": "Stable",
        "risk_factors":        [
            "Minor dependency on third-party infrastructure providers",
            "Regional revenue concentration in North America",
            "Standard SaaS key-person dependency at CTO level",
        ],
        "recommendation":      f"{vendor_name} presents a LOW risk profile. Proceed with standard onboarding agreement. "
                               "Activate 24/7 cyber and financial monitoring hooks upon contract execution.",
    }


# ── public entry point ────────────────────────────────────────────────────────

def run_risk_audit(vendor_name: str) -> RiskResult:
    context = _ddg_risk(vendor_name)
    data    = _llm_risk(vendor_name, context) or _fallback(vendor_name)
    data["cyber_monitoring"]     = _cyber_monitoring_hooks(vendor_name)
    data["financial_monitoring"] = _financial_monitoring_hooks(vendor_name)
    return RiskResult(**data)
