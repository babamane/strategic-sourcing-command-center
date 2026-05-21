from services.llm_service import generate_ai_text

def generate_mitigation_plan(results: list) -> str:
    """
    Generates a high-quality risk mitigation plan using the unified LLM service.
    """
    prompt = f"""
    You are a senior third-party risk management and procurement compliance expert.
    Based on the following vendor risk assessment results:
    {results}

    Generate a detailed Risk Mitigation and Remediation Plan including:
    1. Critical mitigation actions: Actionable fixes for high-risk vulnerabilities/exposures.
    2. Procurement controls: Restrictions or guidelines for onboarding.
    3. Remediation roadmap: Timeline (Immediate, Mid-term, Long-term) for the vendor.
    4. Contractual protections: SLAs, indemnity clauses, and liability limits.

    Format the plan cleanly in professional markdown.
    """
    return generate_mitigation_plan_text(prompt)

def generate_mitigation_plan_text(prompt: str) -> str:
    return generate_ai_text(prompt)