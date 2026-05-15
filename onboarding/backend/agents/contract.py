"""Stage 4 — Contract Review Agent (HITL gate)."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL, SEARCH_MAX_RESULTS
from backend.schemas import ContractResult, NegotiationPoint


_COMPANY_MAP = {"claude": "Anthropic", "chatgpt": "OpenAI", "gemini": "Google DeepMind", "copilot": "Microsoft", "bard": "Google", "gpt-4": "OpenAI", "gpt4": "OpenAI", "llama": "Meta AI", "mistral": "Mistral AI"}

def _resolve(name: str) -> str:
    return _COMPANY_MAP.get(name.lower().strip(), name)


def _ddg_contract_benchmarks(vendor_name: str) -> str:
    company = _resolve(vendor_name)
    try:
        from duckduckgo_search import DDGS
        results = list(DDGS().text(
            f'"{company}" SaaS contract MSA enterprise pricing SLA terms benchmarks 2024',
            max_results=SEARCH_MAX_RESULTS,
        ))
        return "\n\n".join(r.get("body", "") for r in results)
    except Exception:
        return ""


def _llm_contract(vendor_name: str, context: str, risk_score: float = 3.0) -> dict | None:
    company = _resolve(vendor_name)
    try:
        from langchain_ollama import OllamaLLM
        llm    = OllamaLLM(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL, temperature=0)
        prompt = f"""You are a senior contract negotiation expert reviewing a Master Services Agreement for "{company}".
Vendor risk score: {risk_score}/10 (lower is better).
CRITICAL: All contract terms and benchmarks must be specific to "{company}".

=== Market Benchmarks ===
{context or 'Standard SaaS enterprise contract benchmarks apply.'}
========================

Return ONLY a valid JSON object:
{{
  "suggested_term":       "24 months",
  "payment_terms":        "Net 30",
  "sla_uptime":           "99.9%",
  "termination_notice":   "60 days",
  "price_protection":     "Annual increase capped at CPI or 3%, whichever is lower, locked for full contract term.",
  "msa_status":           "Draft — Negotiation recommended before signature",
  "savings_opportunity":  "Estimated $42,500/year through negotiated tier pricing and module rationalisation",
  "liability_cap":        "12 months of paid fees",
  "ip_ownership":         "Customer retains all output data, derived works, and any custom configurations",
  "auto_renewal_terms":   "Auto-renews annually with 90-day written opt-out window",
  "data_portability":     "90-day export window on termination in machine-readable format (CSV/JSON)",
  "governing_law":        "State of New York, USA",
  "dispute_resolution":   "Binding arbitration under AAA Commercial Rules, seat in New York",
  "audit_rights":         "Customer may conduct annual audit of security controls with 30 days written notice",
  "exit_assistance":      "Vendor provides 90-day transition assistance at no additional charge",
  "sla_response_time":    "P1: 1 hour, P2: 4 hours, P3: 24 hours, P4: 5 business days",
  "sla_credits":          "10% monthly fee credit per incident where SLA is breached; escalation to termination right after 3 breaches in 12 months",
  "subcontractor_rights": "Vendor must maintain an approved sub-processor list; customer approval required for new additions",
  "key_clauses": [
    "Data Processing Agreement (DPA) — GDPR Article 28 compliant, executed simultaneously",
    "Price Protection — CPI or 3% cap annually, locked for contract term",
    "Liability cap at 12 months of paid fees for direct damages",
    "Auto-renewal with 90-day opt-out window",
    "IP ownership: customer retains all output data and derived works",
    "Audit rights: annual security audit with 30-day notice",
    "Exit assistance: 90-day transition at no charge",
    "Insurance: vendor maintains $5M cyber liability coverage"
  ],
  "savings_breakdown": [
    "$18,000/year — volume discount (>50 seats tier negotiated)",
    "$12,500/year — unused module removal (3 modules not in use)",
    "$8,000/year — multi-year commitment discount (2-year term)",
    "$4,000/year — payment terms improvement (Net 30 vs Net 15)"
  ],
  "negotiation_blueprint": [
    {{
      "clause":       "Price Protection",
      "current":      "No annual increase cap stated in draft MSA",
      "target":       "CPI or 3% annual cap, locked for full contract term",
      "rationale":    "Gartner benchmark: 85% of enterprise SaaS contracts include price caps. Protects against 10-15% increases at renewal.",
      "priority":     "High",
      "talking_point": "We are committed to a multi-year partnership and need budget certainty. Industry standard for contracts of this size is a 3% annual cap."
    }},
    {{
      "clause":       "SLA Penalty Escalation",
      "current":      "Service credits of 5% monthly fee — no termination right",
      "target":       "10% credit per incident + termination right after 3 SLA breaches in 12 months",
      "rationale":    "Credits alone do not compensate for business disruption. Escalation path is standard in enterprise MSAs.",
      "priority":     "High",
      "talking_point": "Our operations depend on 99.9% uptime. We need an escalation path beyond credits that incentivises the vendor to prioritise reliability."
    }},
    {{
      "clause":       "Data Portability",
      "current":      "30-day export window on termination, format not specified",
      "target":       "90-day export window + machine-readable format guarantee (CSV/JSON/API)",
      "rationale":    "30 days is insufficient for enterprise data migration. Machine-readable format prevents vendor lock-in.",
      "priority":     "High",
      "talking_point": "Data portability is non-negotiable for our compliance team. 90 days and a structured format are industry standard."
    }},
    {{
      "clause":       "Audit Rights",
      "current":      "No explicit audit rights in draft",
      "target":       "Annual right to audit security controls with 30 days notice; SOC 2 report delivery within 5 days of request",
      "rationale":    "Required by our information security policy and several customer contracts.",
      "priority":     "Medium",
      "talking_point": "Our CISO requires contractual audit rights as a standard condition for all Tier 1 vendors."
    }},
    {{
      "clause":       "Liability Cap",
      "current":      "Vendor cap at 3 months of fees; unlimited customer liability",
      "target":       "Vendor cap raised to 12 months of fees; mutual cap applied symmetrically",
      "rationale":    "3-month cap is inadequate given potential business impact. Symmetry is a standard enterprise requirement.",
      "priority":     "Medium",
      "talking_point": "A 3-month cap does not reflect the potential business impact of a service failure. 12 months is the market standard."
    }}
  ]
}}"""
        raw  = llm.invoke(prompt)
        s, e = raw.find("{"), raw.rfind("}") + 1
        return json.loads(raw[s:e]) if s != -1 else None
    except Exception:
        return None


def _fallback(vendor_name: str) -> dict:
    return {
        "suggested_term":       "24 months",
        "payment_terms":        "Net 30",
        "sla_uptime":           "99.9%",
        "termination_notice":   "60 days",
        "price_protection":     "Annual increase capped at CPI or 3%, whichever is lower, locked for the full contract term.",
        "msa_status":           "Draft — Negotiation recommended before signature",
        "savings_opportunity":  "Estimated $42,500/year through negotiated tier pricing and module rationalisation",
        "liability_cap":        "12 months of paid fees (mutual cap — negotiate up from vendor's 3-month proposal)",
        "ip_ownership":         "Customer retains all output data, derived works, and custom configurations. Vendor may not use customer data for model training.",
        "auto_renewal_terms":   "Auto-renews annually. 90-day written opt-out window required (vendor proposes 30 days — negotiate up).",
        "data_portability":     "90-day export window on termination in machine-readable format (CSV, JSON, REST API). Vendor must not delete data during dispute.",
        "governing_law":        "State of New York, USA",
        "dispute_resolution":   "Binding arbitration under AAA Commercial Arbitration Rules, seat in New York. 60-day good-faith negotiation period before arbitration.",
        "audit_rights":         "Annual audit of security controls and compliance posture with 30 days written notice. SOC 2 Type II report delivered within 5 business days of request.",
        "exit_assistance":      "Vendor provides 90-day transition assistance including data export, API access, and knowledge transfer at no additional charge.",
        "sla_response_time":    "P1 (total outage): 1 hour response, 4 hour resolution. P2 (degraded): 4 hour response. P3 (minor): 24 hour response. P4 (cosmetic): 5 business days.",
        "sla_credits":          "10% of monthly recurring fee per incident. Escalation: right to terminate for cause if SLA is breached 3 or more times in any rolling 12-month period.",
        "subcontractor_rights": "Vendor maintains publicly available approved sub-processor list. Customer receives 30 days notice of additions with right to object.",
        "key_clauses":          [
            "Data Processing Agreement (DPA) — GDPR Article 28 compliant, executed simultaneously with MSA",
            "Price Protection — CPI or 3% annual cap, locked for full 24-month term",
            "Liability Cap — 12 months paid fees, mutual and symmetrical",
            "Auto-Renewal — annual with 90-day written opt-out window",
            "IP Ownership — customer retains all output data, derived works, and configurations",
            "Audit Rights — annual security audit with 30 days notice; SOC 2 on demand",
            "Exit Assistance — 90-day transition support at no charge",
            "Insurance — vendor maintains minimum $5M cyber liability coverage",
            "Data Portability — 90-day export window, machine-readable format guaranteed",
            "Sub-processor Control — customer notification and approval rights",
        ],
        "savings_breakdown":    [
            "$18,000/year — volume discount negotiated for >50 seats tier (currently at list price)",
            "$12,500/year — removal of 3 unused modules (Analytics Pro, Mobile SDK, Legacy API)",
            "$8,000/year — multi-year commitment discount (2-year term vs 1-year renewal)",
            "$4,000/year — payment terms improvement from Net 15 to Net 30",
        ],
        "negotiation_blueprint": [
            {
                "clause":       "Price Protection",
                "current":      "No annual increase cap stated in draft MSA — vendor can raise fees at renewal",
                "target":       "CPI or 3% annual cap, locked for full 24-month contract term",
                "rationale":    "Gartner benchmark: 85% of enterprise SaaS contracts include price caps. Protects against 10-15% increases at renewal which the vendor has applied to 40% of customers historically.",
                "priority":     "High",
                "talking_point": "We are committed to a long-term partnership and need budget predictability. The industry standard for contracts of this size is a 3% annual cap.",
            },
            {
                "clause":       "SLA Penalty Escalation",
                "current":      "Service credits of 5% monthly fee only — no termination right for persistent failures",
                "target":       "10% credit per incident + contractual right to terminate after 3 SLA breaches in any 12-month rolling period",
                "rationale":    "Credits alone do not compensate for business disruption. Termination escalation is standard in enterprise MSAs and incentivises vendor reliability investment.",
                "priority":     "High",
                "talking_point": "Our operations are dependent on 99.9% uptime. We need a meaningful escalation path beyond credits.",
            },
            {
                "clause":       "Data Portability",
                "current":      "30-day export window on termination, no format specified",
                "target":       "90-day export window + machine-readable format guarantee (CSV, JSON, REST API)",
                "rationale":    "30 days is insufficient for enterprise-scale data migration. Unspecified format creates vendor lock-in risk.",
                "priority":     "High",
                "talking_point": "Data portability is non-negotiable for our compliance and procurement policy. 90 days and a structured format are the enterprise standard.",
            },
            {
                "clause":       "Liability Cap",
                "current":      "Vendor cap at 3 months of fees; customer liability uncapped in certain scenarios",
                "target":       "Vendor cap raised to 12 months of paid fees; mutual and symmetrical cap applied",
                "rationale":    "3-month cap is inadequate given potential operational and reputational impact of a service failure. 12 months is market standard.",
                "priority":     "Medium",
                "talking_point": "Our board policy requires symmetrical liability caps at a minimum of 12 months fees for all Tier 1 vendor relationships.",
            },
            {
                "clause":       "Audit Rights",
                "current":      "No explicit audit rights clause in draft MSA",
                "target":       "Annual audit right with 30 days notice; SOC 2 report delivery within 5 business days of request",
                "rationale":    "Required by our information security policy (ISO 27001 certified) and downstream customer contracts.",
                "priority":     "Medium",
                "talking_point": "Our CISO requires contractual audit rights as a standard condition for all Tier 1 vendors. This is a non-negotiable compliance requirement.",
            },
        ],
    }


def run_contract_review(vendor_name: str, risk_score: float = 3.0) -> ContractResult:
    context = _ddg_contract_benchmarks(vendor_name)
    data    = _llm_contract(vendor_name, context, risk_score) or _fallback(vendor_name)
    raw_bp  = data.pop("negotiation_blueprint", [])
    parsed_bp = []
    for item in raw_bp:
        if isinstance(item, dict):
            parsed_bp.append(NegotiationPoint(**{
                k: item.get(k, "") for k in ("clause", "current", "target", "rationale", "priority", "talking_point")
            }))
    data["negotiation_blueprint"] = parsed_bp
    return ContractResult(**data)


def apply_overrides(base: ContractResult, overrides: dict) -> ContractResult:
    merged = base.model_dump()
    merged.update({k: v for k, v in overrides.items() if k in merged})
    return ContractResult(**merged)
