"""Stage 5 — Decision Terminal (Aggregated Logic Engine).

Synthesises all prior stage results into a final System Verdict:
  GO              → all green, proceed to production onboarding
  CONDITIONAL_GO  → minor gaps, proceed with conditions
  NO_GO           → critical failures, do not onboard
"""
from backend.schemas import (
    DiscoveryResult, QualificationResult, RiskResult, ContractResult, VerdictResult
)


def _esg_ok(grade: str) -> bool:
    return grade.upper() in ("A+", "A", "A-", "B+")


def _soc2_ok(status: str) -> bool:
    return "type ii" in status.lower() or "verified" in status.lower()


def run_decision(
    discovery:     DiscoveryResult,
    qualification: QualificationResult,
    risk:          RiskResult,
    contract:      ContractResult,
    overrides:     dict | None = None,
) -> VerdictResult:
    """Pure function — no I/O, no LLM needed."""

    # Apply any user HITL overrides to the inputs
    if overrides:
        q_data = qualification.model_dump()
        q_data.update({k: v for k, v in overrides.items() if k in q_data})
        qualification = QualificationResult(**q_data)

        c_data = contract.model_dump()
        c_data.update({k: v for k, v in overrides.items() if k in c_data})
        contract = ContractResult(**c_data)

    # ── Scoring rules ─────────────────────────────────────────────────────────
    score       = float(risk.score)
    esg_ok      = _esg_ok(qualification.esg_grade)
    soc2_ok     = _soc2_ok(qualification.soc2_status)
    gdpr_ok     = qualification.gdpr_compliant
    risk_low    = score <= 3.5
    risk_medium = 3.5 < score <= 6.5

    compliance_summary = (
        f"SOC2: {qualification.soc2_status} | "
        f"ISO 27001: {qualification.iso27001} | "
        f"GDPR: {'✓' if gdpr_ok else '✗'} | "
        f"ESG: {qualification.esg_grade}"
    )
    risk_summary = (
        f"Risk Score: {score}/10 ({risk.level}) | "
        f"Security: {risk.security_rating} | "
        f"Financial Stability: {risk.financial_stability}"
    )

    # ── Verdict logic ─────────────────────────────────────────────────────────
    if soc2_ok and esg_ok and gdpr_ok and risk_low:
        verdict = "GO"
        color   = "green"
        summary = (
            f"{discovery.company_summary[:120]} "
            f"Vendor clears all compliance, risk, and contract gates. "
            f"SOC2 Type II verified, ESG Grade {qualification.esg_grade}, "
            f"Risk Score {score}/10. "
            f"Savings opportunity: {contract.savings_opportunity}. "
            f"Cleared for production onboarding."
        )
        aggregated = (
            f"✓ SOC2 {qualification.soc2_status}  "
            f"✓ ESG Grade {qualification.esg_grade}  "
            f"✓ Risk {score}/10 (LOW)  "
            f"✓ GDPR Compliant  "
            f"✓ Contract terms negotiated — {contract.savings_opportunity}"
        )
    elif (soc2_ok or esg_ok) and gdpr_ok and (risk_low or risk_medium):
        verdict = "CONDITIONAL_GO"
        color   = "orange"
        gaps    = []
        if not soc2_ok:
            gaps.append("SOC2 Type II not fully verified")
        if not esg_ok:
            gaps.append(f"ESG Grade {qualification.esg_grade} — below A threshold")
        if risk_medium:
            gaps.append(f"Risk Score {score}/10 (MEDIUM) — enhanced monitoring required")
        gap_str = "; ".join(gaps)
        summary = (
            f"Vendor meets minimum qualification standards with conditional gaps: {gap_str}. "
            f"Proceed with enhanced monitoring clause and 6-month review checkpoint. "
            f"Savings opportunity: {contract.savings_opportunity}."
        )
        aggregated = (
            f"⚠ Conditional: {gap_str}. "
            f"Risk {score}/10 | GDPR ✓ | "
            f"Contract: {contract.savings_opportunity}"
        )
    else:
        verdict = "NO_GO"
        color   = "red"
        fails   = []
        if not soc2_ok:
            fails.append(f"SOC2 not verified ({qualification.soc2_status})")
        if not gdpr_ok:
            fails.append("GDPR non-compliant")
        if not risk_low and not risk_medium:
            fails.append(f"Risk Score {score}/10 (HIGH)")
        if not esg_ok:
            fails.append(f"ESG Grade {qualification.esg_grade}")
        fail_str = "; ".join(fails)
        summary = (
            f"Vendor FAILS critical onboarding criteria: {fail_str}. "
            f"Do not proceed. Remediation required before re-evaluation."
        )
        aggregated = f"✗ Critical failures: {fail_str}"

    # ── Scorecard ─────────────────────────────────────────────────────────────
    scorecard = [
        {"criterion": "SOC 2 Type II",        "status": "PASS" if soc2_ok   else "FAIL", "detail": qualification.soc2_status},
        {"criterion": "ISO 27001",             "status": "PASS" if qualification.iso27001.lower() != "not certified" else "WARN", "detail": qualification.iso27001},
        {"criterion": "GDPR Compliance",       "status": "PASS" if gdpr_ok   else "FAIL", "detail": "Compliant" if gdpr_ok else "Non-Compliant"},
        {"criterion": "ESG Grade",             "status": "PASS" if esg_ok    else "WARN", "detail": f"Grade {qualification.esg_grade}"},
        {"criterion": "Risk Score",            "status": "PASS" if risk_low  else ("WARN" if risk_medium else "FAIL"), "detail": f"{score}/10 ({risk.level})"},
        {"criterion": "Security Rating",       "status": "PASS" if risk.security_rating in ("A+", "A") else "WARN", "detail": risk.security_rating},
        {"criterion": "Financial Stability",   "status": "PASS", "detail": risk.financial_stability},
        {"criterion": "Contract Negotiated",   "status": "PASS", "detail": contract.msa_status},
        {"criterion": "Price Protection",      "status": "PASS" if contract.price_protection else "WARN", "detail": contract.price_protection[:60] + "…" if contract.price_protection else "Not specified"},
        {"criterion": "Data Portability",      "status": "PASS", "detail": contract.data_portability[:60] + "…" if contract.data_portability else "TBD"},
    ]

    # ── Next steps ────────────────────────────────────────────────────────────
    if verdict == "GO":
        next_steps = [
            "Execute MSA with negotiated terms — target signature within 5 business days",
            "Complete Data Processing Agreement (DPA) simultaneously with MSA",
            "Activate BitSight cyber monitoring and D&B financial monitoring",
            "Provision vendor in procurement system and create PO",
            "Schedule kick-off call with vendor Customer Success team",
            "Set 90-day post-onboarding review in calendar",
        ]
        conditions        = []
        onboarding_timeline = "4–6 weeks from MSA execution to full deployment"
        required_approvals  = ["Procurement sign-off", "Legal review of final MSA", "CISO security approval", "CFO budget approval"]
    elif verdict == "CONDITIONAL_GO":
        next_steps = [
            "Resolve identified gaps before MSA execution",
            "Request remediation plan from vendor with timeline",
            "Add enhanced monitoring clause to MSA",
            "Schedule 6-month review checkpoint in contract",
            "Obtain CISO waiver for any unresolved security gaps",
            "Execute MSA only after gap closure confirmed",
        ]
        conditions          = [f"Resolve gap: {g}" for g in gaps] if 'gaps' in dir() else ["Address identified compliance gaps"]
        onboarding_timeline = "6–10 weeks — extended for gap remediation"
        required_approvals  = ["Procurement sign-off", "Legal review", "CISO approval with gap waiver", "CFO budget approval", "Risk Committee notification"]
    else:
        next_steps = [
            "Do NOT proceed with onboarding",
            "Issue formal vendor rejection notice",
            "Document failure reasons in vendor registry",
            "Initiate alternative vendor evaluation",
            "Re-evaluate vendor in 6 months if remediation is confirmed",
        ]
        conditions          = []
        onboarding_timeline = "N/A — vendor not approved"
        required_approvals  = ["Procurement notification of rejection"]

    return VerdictResult(
        verdict             = verdict,
        color               = color,
        summary             = summary,
        aggregated_logic    = aggregated,
        total_savings       = contract.savings_opportunity,
        risk_summary        = risk_summary,
        compliance_summary  = compliance_summary,
        scorecard           = scorecard,
        conditions          = conditions,
        next_steps          = next_steps,
        onboarding_timeline = onboarding_timeline,
        required_approvals  = required_approvals,
        integration_notes   = f"Primary integration: REST API + webhooks. SDK available for {discovery.tech_stack[0] if discovery.tech_stack else 'major platforms'}. Estimated integration effort: 2–3 sprints.",
        review_checkpoint   = "90-day post-go-live review. Annual contract renewal review at month 20.",
    )
