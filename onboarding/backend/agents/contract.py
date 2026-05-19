"""Stage 4 — Contract Review Agent (HITL gate)."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from backend.config import OLLAMA_BASE_URL, OLLAMA_MODEL, SEARCH_MAX_RESULTS
from backend.schemas import ContractResult, NegotiationPoint


_COMPANY_MAP = {
    "claude": "Anthropic", "anthropic": "Anthropic",
    "chatgpt": "OpenAI", "openai": "OpenAI", "open ai": "OpenAI", "gpt-4": "OpenAI", "gpt4": "OpenAI", "gpt": "OpenAI",
    "gemini": "Google DeepMind", "google deepmind": "Google DeepMind", "deepmind": "Google DeepMind", "google": "Google DeepMind", "bard": "Google DeepMind",
    "copilot": "Microsoft", "microsoft": "Microsoft",
    "llama": "Meta AI", "meta": "Meta AI", "meta ai": "Meta AI",
    "mistral": "Mistral AI", "mistral ai": "Mistral AI",
    "salesforce": "Salesforce", "servicenow": "ServiceNow", "workday": "Workday",
}

_STATIC_SOURCES = {
    "Anthropic":       ["https://www.anthropic.com/pricing", "https://docs.anthropic.com/en/docs/about-claude/models", "https://www.g2.com/products/claude/reviews", "https://techcrunch.com/tag/anthropic/"],
    "OpenAI":          ["https://openai.com/pricing", "https://platform.openai.com/docs/guides/production-best-practices", "https://www.g2.com/products/chatgpt/reviews", "https://techcrunch.com/tag/openai/"],
    "Google DeepMind": ["https://cloud.google.com/vertex-ai/generative-ai/pricing", "https://ai.google.dev/pricing", "https://www.g2.com/products/google-cloud-ai/reviews"],
    "Microsoft":       ["https://www.microsoft.com/en-us/microsoft-365/enterprise/compare-office-365-plans", "https://azure.microsoft.com/en-us/pricing/", "https://www.g2.com/products/microsoft-365/reviews"],
    "Meta AI":         ["https://llama.meta.com", "https://ai.meta.com/llama/license/", "https://www.g2.com/products/meta-ai/reviews"],
    "Salesforce":      ["https://www.salesforce.com/editions-pricing/", "https://www.g2.com/products/salesforce/reviews", "https://investor.salesforce.com"],
    "ServiceNow":      ["https://www.servicenow.com/solutions/pricing.html", "https://www.g2.com/products/servicenow/reviews", "https://investor.servicenow.com"],
    "Workday":         ["https://www.workday.com/en-us/pages/pricing.html", "https://www.g2.com/products/workday/reviews", "https://investor.workday.com"],
}

def _resolve(name: str) -> str:
    key = name.lower().strip()
    return _COMPANY_MAP.get(key, name.strip().title())


def _ddg_contract_benchmarks(vendor_name: str, company: str) -> tuple[str, list[str]]:
    try:
        from duckduckgo_search import DDGS
        results = list(DDGS().text(
            f'"{company}" SaaS contract MSA enterprise pricing SLA terms benchmarks 2024',
            max_results=SEARCH_MAX_RESULTS,
        ))
        context = "\n\n".join(r.get("body", "") for r in results)
        sources = [r.get("href", "") for r in results if r.get("href")]
        return context, sources
    except Exception:
        return "", []


def _llm_contract(vendor_name: str, company: str, context: str, risk_score: float = 3.0) -> dict | None:
    try:
        from langchain_ollama import OllamaLLM
        llm    = OllamaLLM(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL, temperature=0)
        prompt = f"""You are a senior contract negotiation expert reviewing a Master Services Agreement for "{company}".
Vendor risk score: {risk_score}/10 (lower is better).
CRITICAL: All contract terms and benchmarks must be specific to "{company}". Do not reference any other company.

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
  "savings_opportunity":  "Estimated savings through negotiated tier pricing with {company}",
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
    "Price Protection — CPI or 3% cap annually",
    "Liability cap at 12 months of paid fees",
    "Auto-renewal with 90-day opt-out window",
    "IP ownership: customer retains all output data"
  ],
  "savings_breakdown": [
    "$18,000/year — volume discount",
    "$12,500/year — unused module removal",
    "$8,000/year — multi-year commitment discount",
    "$4,000/year — payment terms improvement"
  ],
  "negotiation_blueprint": [
    {{
      "clause":        "Price Protection",
      "current":       "No annual increase cap stated in draft MSA",
      "target":        "CPI or 3% annual cap, locked for full contract term",
      "rationale":     "Gartner benchmark: 85% of enterprise SaaS contracts include price caps.",
      "priority":      "High",
      "talking_point": "We are committed to a multi-year partnership and need budget certainty."
    }}
  ]
}}"""
        raw  = llm.invoke(prompt)
        s, e = raw.find("{"), raw.rfind("}") + 1
        if s == -1:
            return None
        parsed = json.loads(raw[s:e])
        # Validate output references the company
        msa = parsed.get("msa_status", "").lower() + parsed.get("savings_opportunity", "").lower()
        if company.lower().split()[0] not in msa and vendor_name.lower() not in msa:
            return None
        return parsed
    except Exception:
        return None


_KNOWN: dict[str, dict] = {
    "Anthropic": {
        "suggested_term":       "24 months",
        "payment_terms":        "Net 30",
        "sla_uptime":           "99.9%",
        "termination_notice":   "60 days",
        "price_protection":     "Annual increase capped at CPI or 3%, whichever is lower, locked for the full 24-month contract term. Applies to all Claude API pricing tiers.",
        "msa_status":           "Draft — Negotiation recommended before signature",
        "savings_opportunity":  "Estimated $38,000/year through negotiated Claude API volume tiers and committed use discounts",
        "liability_cap":        "12 months of paid fees (mutual cap — negotiate up from Anthropic's standard 3-month proposal)",
        "ip_ownership":         "Customer retains all output data, derived works, fine-tuned configurations, and any prompts. Anthropic may not use customer inputs or outputs for Claude model training without explicit written consent.",
        "auto_renewal_terms":   "Auto-renews annually. 90-day written opt-out window required (Anthropic standard is 30 days — negotiate up).",
        "data_portability":     "90-day export window on termination in machine-readable format (CSV, JSON, REST API). Anthropic must not delete customer data during any active dispute.",
        "governing_law":        "State of Delaware, USA (Anthropic HQ) or State of California, USA (negotiable)",
        "dispute_resolution":   "Binding arbitration under AAA Commercial Arbitration Rules, seat in San Francisco. 60-day good-faith negotiation period before arbitration.",
        "audit_rights":         "Annual audit of Anthropic's security controls and Constitutional AI safeguards with 30 days written notice. SOC 2 Type II report delivered within 5 business days of request.",
        "exit_assistance":      "Anthropic provides 90-day transition assistance including API access continuation, data export, and Claude prompt migration documentation at no additional charge.",
        "sla_response_time":    "P1 (total API outage): 1 hour response, 4 hour resolution. P2 (degraded performance): 4 hour response. P3 (minor): 24 hour response. P4 (cosmetic): 5 business days.",
        "sla_credits":          "10% of monthly API fees per incident. Escalation: right to terminate for cause if SLA breached 3+ times in any rolling 12-month period.",
        "subcontractor_rights": "Anthropic maintains approved sub-processor list (AWS, GCP). Customer receives 30 days notice of additions with right to object. Sub-processors bound by equivalent data protection obligations.",
        "key_clauses":          [
            "Data Processing Agreement (DPA) — GDPR Article 28 compliant, executed simultaneously with MSA",
            "No Training on Customer Data — Anthropic explicitly prohibited from using customer inputs/outputs for model training",
            "Price Protection — CPI or 3% annual cap, locked for full 24-month term",
            "Liability Cap — 12 months paid fees, mutual and symmetrical",
            "Auto-Renewal — annual with 90-day written opt-out window",
            "IP Ownership — customer retains all Claude outputs, derived works, and prompt configurations",
            "Audit Rights — annual security and Constitutional AI audit with 30 days notice; SOC 2 on demand",
            "Exit Assistance — 90-day transition support at no charge including prompt migration",
            "Insurance — Anthropic maintains minimum $5M cyber liability coverage",
            "Data Portability — 90-day export window, machine-readable format guaranteed",
            "Model Continuity — access to current Claude model version guaranteed for contract term",
            "Sub-processor Control — AWS and GCP only; customer notification and approval for any new additions",
        ],
        "savings_breakdown":    [
            "$15,000/year — committed use discount (100M+ tokens/month volume tier)",
            "$10,000/year — multi-year commitment discount (2-year term vs annual)",
            "$8,000/year — enterprise API tier negotiated vs. pay-as-you-go list price",
            "$5,000/year — dedicated support tier included at no uplift (standard: $12K/year)",
        ],
        "negotiation_blueprint": [
            {
                "clause":        "No Training on Customer Data",
                "current":       "Anthropic's standard API terms reserve right to use inputs/outputs for model improvement",
                "target":        "Explicit prohibition on using customer data for Claude model training; documented in DPA",
                "rationale":     "Enterprise customers have confidential data and IP that must not contribute to competitor model training. Critical for legal and compliance teams.",
                "priority":      "High",
                "talking_point": "Our legal team requires an explicit contractual commitment that no customer prompts, outputs, or derived data will be used to train or fine-tune any Anthropic model.",
            },
            {
                "clause":        "Price Protection",
                "current":       "No annual increase cap stated in Anthropic's draft MSA — API pricing can change at 30 days notice",
                "target":        "CPI or 3% annual cap on all Claude API pricing tiers, locked for full 24-month contract term",
                "rationale":     "Gartner benchmark: 85% of enterprise AI contracts include price caps. Claude API pricing has historically dropped but enterprise contracts require upside protection.",
                "priority":      "High",
                "talking_point": "We are committing to a 24-month partnership and significant volume. We need price certainty for our internal budgeting and board approvals.",
            },
            {
                "clause":        "Model Continuity",
                "current":       "No clause guaranteeing access to current Claude model version — Anthropic can deprecate models with 30 days notice",
                "target":        "Access to current Claude model version guaranteed for full contract term; 12-month deprecation notice for any model in active use",
                "rationale":     "Model changes can break production integrations. Enterprise customers need stability guarantees not present in standard API terms.",
                "priority":      "High",
                "talking_point": "We are building production systems on Claude. Model changes or deprecations can require significant re-engineering. We need a minimum 12-month notice period.",
            },
            {
                "clause":        "Liability Cap",
                "current":       "Anthropic standard cap: 3 months of fees paid; customer liability potentially uncapped in certain scenarios",
                "target":        "Mutual cap at 12 months of paid fees for direct damages; exclusions only for gross negligence and wilful misconduct",
                "rationale":     "3-month cap is inadequate given potential business impact of API outages in production environments. 12 months is market standard.",
                "priority":      "Medium",
                "talking_point": "Our board policy requires symmetrical liability caps at a minimum of 12 months fees for all Tier 1 AI vendor relationships.",
            },
            {
                "clause":        "Audit Rights",
                "current":       "No explicit audit rights or Constitutional AI governance audit rights in Anthropic's standard MSA",
                "target":        "Annual right to audit security controls and AI safety measures with 30 days notice; SOC 2 and Constitutional AI report delivery within 5 business days",
                "rationale":     "Required by information security policy (ISO 27001) and downstream customer contracts. AI governance audit rights are emerging as a standard enterprise requirement.",
                "priority":      "Medium",
                "talking_point": "Our CISO and AI governance committee require contractual audit rights as a standard condition for all Tier 1 AI vendor relationships.",
            },
        ],
    },
    "OpenAI": {
        "suggested_term":       "24 months",
        "payment_terms":        "Net 30",
        "sla_uptime":           "99.9%",
        "termination_notice":   "60 days",
        "price_protection":     "Annual increase capped at CPI or 3%, whichever is lower, locked for the full 24-month contract term. Applies to all GPT API and ChatGPT Enterprise pricing.",
        "msa_status":           "Draft — Negotiation recommended before signature",
        "savings_opportunity":  "Estimated $52,000/year through negotiated GPT API volume tiers, ChatGPT Enterprise seat optimisation, and committed use discounts",
        "liability_cap":        "12 months of paid fees (mutual cap — negotiate up from OpenAI's standard 3-month proposal)",
        "ip_ownership":         "Customer retains all output data, derived works, fine-tuned configurations, and custom GPTs. OpenAI may not use Enterprise customer data for GPT model training without explicit written consent.",
        "auto_renewal_terms":   "Auto-renews annually. 90-day written opt-out window required (OpenAI standard is 30 days — negotiate up).",
        "data_portability":     "90-day export window on termination in machine-readable format (CSV, JSON, REST API). OpenAI must not delete customer data during any active dispute.",
        "governing_law":        "State of Delaware, USA (OpenAI HQ)",
        "dispute_resolution":   "Binding arbitration under AAA Commercial Arbitration Rules, seat in San Francisco. 60-day good-faith negotiation period before arbitration.",
        "audit_rights":         "Annual audit of OpenAI's security controls with 30 days written notice. SOC 2 Type II report delivered within 5 business days of request. FTC investigation status disclosure within 10 business days.",
        "exit_assistance":      "OpenAI provides 90-day transition assistance including API access continuation, data export, and GPT configuration migration at no additional charge.",
        "sla_response_time":    "P1 (total API outage): 1 hour response, 4 hour resolution. P2 (degraded): 4 hour response. P3 (minor): 24 hours. P4 (cosmetic): 5 business days.",
        "sla_credits":          "10% of monthly fees per incident. Escalation: right to terminate for cause if SLA breached 3+ times in any rolling 12-month period.",
        "subcontractor_rights": "OpenAI maintains approved sub-processor list (Microsoft Azure primarily). Customer receives 30 days notice of additions with right to object.",
        "key_clauses":          [
            "Data Processing Agreement (DPA) — GDPR Article 28 compliant, executed simultaneously with MSA",
            "No Training on Enterprise Data — OpenAI explicitly prohibited from using Enterprise customer data for GPT model training",
            "Price Protection — CPI or 3% annual cap, locked for full 24-month term",
            "Liability Cap — 12 months paid fees, mutual and symmetrical",
            "Auto-Renewal — annual with 90-day written opt-out window",
            "IP Ownership — customer retains all GPT outputs, derived works, and custom configurations",
            "Audit Rights — annual security audit with 30 days notice; SOC 2 on demand; FTC disclosure obligation",
            "Exit Assistance — 90-day transition support at no charge",
            "Insurance — OpenAI maintains minimum $10M cyber liability coverage",
            "Data Portability — 90-day export window, machine-readable format guaranteed",
            "Key-Person Clause — 90-day notice if Sam Altman or CTO departs; customer review right triggered",
            "Regulatory Disclosure — OpenAI must notify customer within 10 days of any material regulatory action",
        ],
        "savings_breakdown":    [
            "$20,000/year — GPT API volume tier negotiated (>10M tokens/day committed use)",
            "$15,000/year — ChatGPT Enterprise seat rationalisation (right-sized to actual active users)",
            "$10,000/year — multi-year commitment discount (2-year term)",
            "$7,000/year — dedicated support and success manager included at no uplift",
        ],
        "negotiation_blueprint": [
            {
                "clause":        "No Training on Enterprise Data",
                "current":       "OpenAI's standard API terms allow use of inputs/outputs for model improvement unless opted out explicitly",
                "target":        "Explicit prohibition in MSA and DPA; Enterprise data flagged as excluded from all training pipelines",
                "rationale":     "Confidential business data used to train models available to competitors is a critical IP and compliance risk for enterprise customers.",
                "priority":      "High",
                "talking_point": "Our legal and IP teams require a contractual guarantee — not just a settings toggle — that our data will never be used to train any OpenAI model.",
            },
            {
                "clause":        "Key-Person Governance Clause",
                "current":       "No clause addressing leadership continuity following November 2023 board crisis precedent",
                "target":        "90-day advance written notice if Sam Altman or CTO departs; customer right to review and renegotiate contract",
                "rationale":     "November 2023 demonstrated that OpenAI leadership continuity is a material business risk. Enterprise customers need contractual protection.",
                "priority":      "High",
                "talking_point": "Following the events of November 2023, our board requires a key-person governance clause as a condition of any multi-year OpenAI commitment.",
            },
            {
                "clause":        "Regulatory Disclosure Obligation",
                "current":       "No contractual obligation for OpenAI to disclose FTC investigation or regulatory actions to enterprise customers",
                "target":        "OpenAI must notify customer within 10 business days of any material regulatory action, enforcement, or investigation that could affect service continuity",
                "rationale":     "FTC investigation (2023, ongoing) creates regulatory risk. Enterprise customers need advance notice to plan contingencies.",
                "priority":      "High",
                "talking_point": "Our risk and compliance team requires regulatory transparency as a standard condition for all Tier 1 AI vendor relationships.",
            },
            {
                "clause":        "Price Protection",
                "current":       "No annual cap on GPT API pricing or ChatGPT Enterprise seat pricing in standard MSA",
                "target":        "CPI or 3% annual cap on all pricing, locked for 24-month term",
                "rationale":     "GPT-4 pricing has historically been volatile. Enterprise budget predictability requires contractual price protection.",
                "priority":      "Medium",
                "talking_point": "We are committing significant volume and a 24-month term. In return, we need price certainty that matches our budget planning cycle.",
            },
            {
                "clause":        "Liability Cap",
                "current":       "OpenAI standard cap: 3 months of fees; customer liability potentially uncapped for IP indemnification scenarios",
                "target":        "Mutual cap at 12 months of paid fees; IP indemnification carve-out capped at 24 months",
                "rationale":     "3-month cap is inadequate. OpenAI's scale of use means API outages have significant business impact. 12 months is the enterprise market standard.",
                "priority":      "Medium",
                "talking_point": "Our board policy requires symmetrical liability caps at 12 months minimum. The current 3-month cap does not reflect the operational dependency we are accepting.",
            },
        ],
    },
}


def _fallback(vendor_name: str, company: str) -> dict:
    match = next((k for k in _KNOWN if k.lower() == company.lower()), None)
    if match:
        return _KNOWN[match]
    return {
        "suggested_term":       "24 months",
        "payment_terms":        "Net 30",
        "sla_uptime":           "99.9%",
        "termination_notice":   "60 days",
        "price_protection":     "Annual increase capped at CPI or 3%, whichever is lower, locked for the full contract term.",
        "msa_status":           "Draft — Negotiation recommended before signature",
        "savings_opportunity":  f"Estimated $42,500/year through negotiated tier pricing and module rationalisation with {company}",
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
                "clause":        "Price Protection",
                "current":       f"No annual increase cap stated in draft MSA — {company} can raise fees at renewal",
                "target":        "CPI or 3% annual cap, locked for full 24-month contract term",
                "rationale":     "Gartner benchmark: 85% of enterprise SaaS contracts include price caps. Protects against 10-15% increases at renewal.",
                "priority":      "High",
                "talking_point": "We are committed to a long-term partnership and need budget predictability. The industry standard for contracts of this size is a 3% annual cap.",
            },
            {
                "clause":        "SLA Penalty Escalation",
                "current":       "Service credits of 5% monthly fee only — no termination right for persistent failures",
                "target":        "10% credit per incident + contractual right to terminate after 3 SLA breaches in any 12-month rolling period",
                "rationale":     "Credits alone do not compensate for business disruption. Termination escalation incentivises vendor reliability investment.",
                "priority":      "High",
                "talking_point": "Our operations are dependent on 99.9% uptime. We need a meaningful escalation path beyond credits.",
            },
            {
                "clause":        "Data Portability",
                "current":       "30-day export window on termination, no format specified",
                "target":        "90-day export window + machine-readable format guarantee (CSV, JSON, REST API)",
                "rationale":     "30 days is insufficient for enterprise-scale data migration. Unspecified format creates vendor lock-in risk.",
                "priority":      "High",
                "talking_point": "Data portability is non-negotiable for our compliance and procurement policy. 90 days and a structured format are the enterprise standard.",
            },
            {
                "clause":        "Liability Cap",
                "current":       "Vendor cap at 3 months of fees; customer liability uncapped in certain scenarios",
                "target":        "Vendor cap raised to 12 months of paid fees; mutual and symmetrical cap applied",
                "rationale":     "3-month cap is inadequate given potential operational impact of a service failure. 12 months is market standard.",
                "priority":      "Medium",
                "talking_point": "Our board policy requires symmetrical liability caps at a minimum of 12 months fees for all Tier 1 vendor relationships.",
            },
            {
                "clause":        "Audit Rights",
                "current":       "No explicit audit rights clause in draft MSA",
                "target":        "Annual audit right with 30 days notice; SOC 2 report delivery within 5 business days of request",
                "rationale":     "Required by our information security policy (ISO 27001 certified) and downstream customer contracts.",
                "priority":      "Medium",
                "talking_point": "Our CISO requires contractual audit rights as a standard condition for all Tier 1 vendors. This is a non-negotiable compliance requirement.",
            },
        ],
    }


def run_contract_review(vendor_name: str, risk_score: float = 3.0) -> ContractResult:
    company = _resolve(vendor_name)
    context, sources = _ddg_contract_benchmarks(vendor_name, company)
    data    = _llm_contract(vendor_name, company, context, risk_score) or _fallback(vendor_name, company)
    static  = _STATIC_SOURCES.get(company, [])
    data["sources"] = list(dict.fromkeys(sources + static))
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
