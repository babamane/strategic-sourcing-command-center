import asyncio
from services.tavily_service import tavily_search
from services.llm_service import generate_ai_text, evaluate_agent_risk_score

async def analyze_esg_risk(vendor_data: dict) -> dict:
    """
    ESG Risk Agent: Evaluates the vendor's Environmental impact, Social practices (e.g. labor compliance), 
    and Corporate Governance integrity.
    """
    company_name = vendor_data.get("company_name", "")
    
    findings = []
    references = []
    risk_score = 0

    try:
        query = f"{company_name} ESG controversy environmental violations labor dispute governance failure carbon footprint sustainability rating"
        response = await asyncio.to_thread(tavily_search, query)
        
        if response.get("results"):
            controversy_count = 0
            for item in response["results"]:
                title = item.get("title", "")
                content = item.get("content", "")
                combined = (title + " " + content).lower()
                
                if any(keyword in combined for keyword in ["pollution", "labor", "governance", "controversy", "esg", "sustainability", "violation", "strike", "lawsuit"]):
                    if controversy_count < 3:
                        findings.append(f"Controversy: {title}")
                        risk_score += 10
                        controversy_count += 1
                
                references.append({
                    "title": title,
                    "url": item.get("url")
                })
    except Exception as e:
        findings.append(f"ESG news search failed: {str(e)}")
        risk_score += 15

    # Final calculations using dynamic LLM/cryptographic risk evaluation
    risk_score = evaluate_agent_risk_score("ESG Risk", company_name, findings, risk_score)
    
    severity = "Low"
    if risk_score >= 75:
        severity = "Critical"
    elif risk_score >= 55:
        severity = "High"
    elif risk_score >= 40:
        severity = "Medium"

    business_impact = (
        "Potential reputational damage, customer backlash, or regulatory penalties due to labor violations "
        "or carbon-emissions non-compliance. Direct impact on brand value."
        if severity in ["High", "Critical"] else
        "Minor ESG exposure. Stable sustainability profile with standard regulatory alignment."
    )

    procurement_impact = (
        "Include ESG requirements in the RFP. Obtain contractual alignment with environmental code of conduct."
        if severity in ["High", "Critical"] else
        "Standard ESG monitoring and alignment. No blockers."
    )

    # Generate AI summary in thread
    prompt = f"""
    You are an enterprise Environmental, Social, and Governance (ESG) risk analyst.
    Summarize the ESG risk profile of {company_name} based on the following findings:
    {findings}
    
    Summarize in 2-3 sentences. Identify if there are severe reputational or environmental issues.
    """
    ai_summary = await asyncio.to_thread(generate_ai_text, prompt)

    return {
        "risk_category": "ESG Risk",
        "risk_score": risk_score,
        "severity": severity,
        "confidence_score": 80 if references else 45,
        "findings": findings if findings else ["No major environmental or governance controversies detected."],
        "references": references[:5],
        "recommendations": [
            "Request ESG policy statements and annual sustainability reports.",
            "Verify labor practices and health & safety compliance standard procedures.",
            "Include carbon-reduction guidelines and code of conduct compliance in contracts."
        ],
        "business_impact": business_impact,
        "procurement_impact": procurement_impact,
        "ai_summary": ai_summary
    }