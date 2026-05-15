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

    return VerdictResult(
        verdict            = verdict,
        color              = color,
        summary            = summary,
        aggregated_logic   = aggregated,
        total_savings      = contract.savings_opportunity,
        risk_summary       = risk_summary,
        compliance_summary = compliance_summary,
    )
