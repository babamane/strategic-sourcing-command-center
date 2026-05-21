import asyncio
from services.gdelt_service import fetch_gdelt_events
from services.tavily_service import tavily_search
from services.llm_service import generate_ai_text, evaluate_agent_risk_score

async def analyze_geopolitical_risk(vendor_data: dict) -> dict:
    """
    Geopolitical & Supply Chain Agent: Assesses supplier location risk, regional instability, 
    trade embargoes, logistics bottlenecks, and macro-economic factors.
    """
    company_name = vendor_data.get("company_name", "")
    
    findings = []
    references = []
    risk_score = 0

    # Run GDELT in thread
    try:
        gdelt_results = await asyncio.to_thread(fetch_gdelt_events, company_name)
        articles = gdelt_results.get("articles", [])
        if len(articles) > 0:
            findings.append(f"GDELT: Geopolitical incidents/news events detected ({len(articles)} events)")
            risk_score += min(len(articles) * 6, 25)
            for item in articles[:2]:
                title = item.get("title", "")
                findings.append(f"GDELT Event: {title}")
                references.append({
                    "title": title,
                    "url": item.get("url")
                })
    except Exception as e:
        pass

    # Run Tavily in thread
    try:
        query = f"{company_name} supply chain disruption regional instability logistics delays import export tariff trade war"
        response = await asyncio.to_thread(tavily_search, query)
        if response.get("results"):
            disruption_count = 0
            for item in response["results"]:
                title = item.get("title", "")
                content = item.get("content", "")
                combined = (title + " " + content).lower()
                
                if any(keyword in combined for keyword in ["disruption", "tariff", "supply chain", "logistic", "trade war", "embargo", "shortage"]):
                    if disruption_count < 3:
                        findings.append(f"Supply chain intel: {title}")
                        risk_score += 10
                        disruption_count += 1
                
                references.append({
                    "title": title,
                    "url": item.get("url")
                })
    except Exception as e:
        pass

    # Final calculations using dynamic LLM/cryptographic risk evaluation
    risk_score = evaluate_agent_risk_score("Geopolitical & Supply Chain", company_name, findings, risk_score)
    
    severity = "Low"
    if risk_score >= 75:
        severity = "Critical"
    elif risk_score >= 55:
        severity = "High"
    elif risk_score >= 40:
        severity = "Medium"

    business_impact = (
        "High risk of critical project delays, material shortages, and increased import costs due to regional "
        "conflict or geopolitical tariffs."
        if severity in ["High", "Critical"] else
        "Standard logistics profile. Minimal localized disruption risk; easily manageable."
    )

    procurement_impact = (
        "Mandate multi-sourcing strategies. Require dual-redundant manufacturing sites outside high-risk jurisdictions."
        if severity in ["High", "Critical"] else
        "Ensure standard delivery guarantees and periodic contingency review."
    )

    # Generate AI summary in thread
    prompt = f"""
    You are a geopolitical and global supply chain risk intelligence expert.
    Summarize the geopolitical and supply chain risk profile of {company_name} based on the following findings:
    {findings}
    
    Summarize in 2-3 sentences. Evaluate regional dependencies if mentioned.
    """
    ai_summary = await asyncio.to_thread(generate_ai_text, prompt)

    return {
        "risk_category": "Geopolitical & Supply Chain",
        "risk_score": risk_score,
        "severity": severity,
        "confidence_score": 85 if references else 50,
        "findings": findings if findings else ["No major geopolitical or supply chain disruptions detected."],
        "references": references[:5],
        "recommendations": [
            "Establish dual-sourcing agreements for critical hardware/software modules.",
            "Monitor regional logistics hubs and maritime trade routes continuously.",
            "Verify alternative shipping/logistics carriers and warehouse distribution locations."
        ],
        "business_impact": business_impact,
        "procurement_impact": procurement_impact,
        "ai_summary": ai_summary
    }