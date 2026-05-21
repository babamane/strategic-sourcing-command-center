from services.llm_service import generate_ai_text

def generate_ai_report(results: list) -> str:
    """
    Generates a high-quality executive summary using the unified LLM service.
    """
    prompt = f"""
    You are a senior strategic sourcing and third-party risk management executive.
    Analyze the following multi-agent vendor risk intelligence results:
    {results}

    Generate a highly strategic, professional, and detailed Executive Risk Intelligence Report including:
    1. Executive Summary: High-level overview of the vendor's operations and risks.
    2. Critical Risk Exposure: Identify specific agents that detected high/critical risks.
    3. Business Impact: Highlight what these risks mean for the business.
    4. Strategic Recommendations: What steps procurement should take.

    Ensure it is written in professional enterprise markdown format.
    """
    return generate_ai_text(prompt)