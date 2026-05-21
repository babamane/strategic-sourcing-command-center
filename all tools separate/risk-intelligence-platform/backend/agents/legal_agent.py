import asyncio
from services.tavily_service import tavily_search
from api_clients.opensanctions_client import fetch_opensanctions_data
from services.llm_service import generate_ai_text, evaluate_agent_risk_score

async def analyze_legal_risk(vendor_data: dict) -> dict:
    """
    Legal & Sanctions Agent: Scans global sanctions databases, PEP listings, regulatory enforcement records, 
    and general litigation history.
    """
    company_name = vendor_data.get("company_name", "")
    
    findings = []
    references = []
    risk_score = 0

    # 1. OpenSanctions MATCH (in thread)
    try:
        sanctions_data = await asyncio.to_thread(fetch_opensanctions_data, company_name)
        if isinstance(sanctions_data, dict) and "warning" not in sanctions_data:
            results = sanctions_data.get("results", [])
            if len(results) > 0:
                match_count = 0
                for match in results:
                    caption = match.get("caption")
                    schema = match.get("schema")
                    features = match.get("properties", {})
                    score = float(match.get("score", 0.5))
                    if score > 0.7:
                        findings.append(f"Sanctions watchlist MATCH: {caption} (Schema: {schema}, Match Score: {score * 100:.1f}%)")
                        risk_score += 40
                        match_count += 1
                        if match_count >= 2:
                            break
            else:
                findings.append("OpenSanctions Database: Checked, no matches on global watchlists.")
        elif isinstance(sanctions_data, dict) and "warning" in sanctions_data:
            findings.append(f"OpenSanctions Check: {sanctions_data['warning']}")
    except Exception as e:
        pass

    # 2. Legal News Search (in thread)
    try:
        query = f"{company_name} lawsuit litigation fraud corruption regulatory fine penalty SEC sanctions"
        response = await asyncio.to_thread(tavily_search, query)
        if response.get("results"):
            legal_count = 0
            for item in response["results"]:
                title = item.get("title", "")
                content = item.get("content", "")
                combined = (title + " " + content).lower()
                
                if any(keyword in combined for keyword in ["lawsuit", "penalty", "sanction", "fraud", "regulatory", "corruption", "litigation"]):
                    if legal_count < 3:
                        findings.append(f"Litigation record: {title}")
                        risk_score += 12
                        legal_count += 1
                
                references.append({
                    "title": title,
                    "url": item.get("url")
                })
    except Exception as e:
        pass

    # Final calculations using dynamic LLM/cryptographic risk evaluation
    risk_score = evaluate_agent_risk_score("Legal & Sanctions", company_name, findings, risk_score)
    
    severity = "Low"
    if risk_score >= 75:
        severity = "Critical"
    elif risk_score >= 55:
        severity = "High"
    elif risk_score >= 40:
        severity = "Medium"

    business_impact = (
        "Potential contract termination, heavy regulatory fines, and legal liability in case of sanctions compliance violations."
        if severity in ["High", "Critical"] else
        "Standard corporate legal exposures. Minor ongoing litigation with low potential of business disruption."
    )

    procurement_impact = (
        "Critical blocker. Stop procurement immediately or request full legal review of sanctions exposure and PEP ties."
        if severity in ["High", "Critical"] else
        "Include standard indemnity clauses and compliance warranties in final contracts."
    )

    # Generate AI summary in thread
    prompt = f"""
    You are a corporate legal and sanctions compliance analyst.
    Summarize the legal and sanctions risk profile of {company_name} based on the following findings:
    {findings}
    
    Summarize in 2-3 sentences. Note any active sanctions watchlist matches or regulatory fraud investigations.
    """
    ai_summary = await asyncio.to_thread(generate_ai_text, prompt)

    return {
        "risk_category": "Legal & Sanctions",
        "risk_score": risk_score,
        "severity": severity,
        "confidence_score": 85 if references else 50,
        "findings": findings if findings else ["No major legal disputes or watchlist exposures detected."],
        "references": references[:5],
        "recommendations": [
            "Perform comprehensive legal due diligence on parent and child entities.",
            "Verify Ultimate Beneficial Owners (UBO) against global sanctions databases.",
            "Incorporate strong termination-for-cause and regulatory compliance clauses in final SLAs."
        ],
        "business_impact": business_impact,
        "procurement_impact": procurement_impact,
        "ai_summary": ai_summary
    }