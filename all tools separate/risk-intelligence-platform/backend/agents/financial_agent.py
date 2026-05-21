import asyncio
from services.financial_service import fetch_financial_data, analyze_financial_risk_service
from services.llm_service import generate_ai_text, evaluate_agent_risk_score

async def analyze_financial_risk(vendor_data: dict) -> dict:
    """
    Financial Risk Agent: Evaluates the vendor's financial stability, profitability, 
    leverage, and liquidity to prevent vendor insolvency risks.
    """
    ticker = vendor_data.get("ticker", "")
    company_name = vendor_data.get("company_name", "")
    
    # Delegate core analysis to service
    analysis = await analyze_financial_risk_service(vendor_data)
    
    risk_score = analysis["risk_score"]
    findings = analysis["findings"]
    financial_data = analysis["financial_data"]

    # Final calculations using dynamic LLM/cryptographic risk evaluation
    risk_score = evaluate_agent_risk_score("Financial Risk", company_name, findings, risk_score)
    
    severity = "Low"
    if risk_score >= 75:
        severity = "Critical"
    elif risk_score >= 55:
        severity = "High"
    elif risk_score >= 40:
        severity = "Medium"
        
    business_impact = (
        "High leverage or low profitability increases the risk of service interruption, "
        "insolvency, or reduced R&D capability, which could affect long-term product support."
        if severity in ["High", "Critical"] else
        "The vendor demonstrates solid financial health, posing low risk to ongoing operations."
    )
    
    procurement_impact = (
        "Require quarterly financial health certificates or escrow agreements. Restrict upfront payments."
        if severity in ["High", "Critical"] else
        "Standard procurement terms apply. No special financial covenants required."
    )

    # Generate Agent AI summary in background thread
    prompt = f"""
    You are an expert corporate financial risk analyst.
    Summarize the financial health of {company_name} (Ticker: {ticker}) based on the following findings:
    {findings}
    
    Keep the summary professional, analytical, and under 3 sentences.
    """
    ai_summary = await asyncio.to_thread(generate_ai_text, prompt)
    
    references = [
        {
            "title": f"Yahoo Finance: {ticker} Profile",
            "url": f"https://finance.yahoo.com/quote/{ticker}"
        }
    ]
    
    return {
        "risk_category": "Financial Risk",
        "risk_score": risk_score,
        "severity": severity,
        "confidence_score": 90 if "error" not in financial_data else 40,
        "findings": findings,
        "references": references,
        "recommendations": [
            "Review audited financial statements annually.",
            "Monitor debt-to-equity and current ratios.",
            "Establish contingency plans for critical service dependencies."
        ],
        "business_impact": business_impact,
        "procurement_impact": procurement_impact,
        "ai_summary": ai_summary
    }