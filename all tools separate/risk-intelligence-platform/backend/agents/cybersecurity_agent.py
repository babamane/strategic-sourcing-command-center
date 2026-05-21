import asyncio
from services.tavily_service import tavily_search
from services.nvd_service import fetch_nvd_vulnerabilities
from services.otx_service import fetch_otx_data
from api_clients.shodan_client import fetch_shodan_data
from services.llm_service import generate_ai_text, evaluate_agent_risk_score

async def analyze_cybersecurity_risk(vendor_data: dict) -> dict:
    """
    Cybersecurity Agent: Evaluates public threat footprint, open ports, historical data breaches,
    active vulnerabilities (CVEs), and security incidents.
    """
    company_name = vendor_data.get("company_name", "")
    domain = vendor_data.get("domain", "")
    
    findings = []
    references = []
    risk_score = 0

    # Run blocking telemetry gatherings concurrently in background threads
    try:
        nvd_results = await asyncio.to_thread(fetch_nvd_vulnerabilities, company_name)
        if isinstance(nvd_results, list) and len(nvd_results) > 0:
            findings.append(f"NVD Database: {len(nvd_results)} CVEs associated with '{company_name}' products")
            risk_score += min(len(nvd_results) * 5, 25)
            for vulnerability in nvd_results[:2]:
                findings.append(f"CVE ID: {vulnerability.get('id')} (Severity: {vulnerability.get('severity')})")
    except Exception as e:
        pass

    try:
        otx_results = await asyncio.to_thread(fetch_otx_data, domain)
        if isinstance(otx_results, dict) and otx_results.get("pulse_count", 0) > 0:
            pulses = otx_results.get("pulse_count", 0)
            findings.append(f"AlienVault OTX: Exposed threat indicators found ({pulses} pulses)")
            risk_score += min(pulses * 3, 20)
    except Exception as e:
        pass

    try:
        shodan_results = await asyncio.to_thread(fetch_shodan_data, domain)
        if isinstance(shodan_results, list) and len(shodan_results) > 0:
            findings.append(f"Shodan: Detected {len(shodan_results)} open ports/exposed services on domain {domain}")
            risk_score += min(len(shodan_results) * 4, 20)
            for item in shodan_results[:2]:
                findings.append(f"Exposed service on IP {item.get('ip')}: Port {item.get('port')} (Service: {item.get('service')})")
        elif isinstance(shodan_results, dict) and "error" in shodan_results:
            findings.append(f"Shodan scan skipped: {shodan_results['error']}")
    except Exception as e:
        pass

    try:
        query = f"{company_name} cybersecurity breach ransomware vulnerability data leak hack"
        tavily_results = await asyncio.to_thread(tavily_search, query)
        if tavily_results.get("results"):
            breach_count = 0
            for item in tavily_results["results"]:
                title = item.get("title", "")
                content = item.get("content", "")
                combined = (title + " " + content).lower()
                
                if any(keyword in combined for keyword in ["breach", "ransomware", "attack", "data leak", "vulnerability", "hack"]):
                    if breach_count < 3:
                        findings.append(f"Breach news: {title}")
                        risk_score += 8
                        breach_count += 1
                
                references.append({
                    "title": title,
                    "url": item.get("url")
                })
    except Exception as e:
        pass

    # Final calculations using dynamic LLM/cryptographic risk evaluation
    risk_score = evaluate_agent_risk_score("Cybersecurity", company_name, findings, risk_score)
    
    severity = "Low"
    if risk_score >= 75:
        severity = "Critical"
    elif risk_score >= 55:
        severity = "High"
    elif risk_score >= 40:
        severity = "Medium"

    business_impact = (
        "High probability of data leakage, credential compromise, or ransomware disruptions. "
        "Could lead to regulatory fines, service outages, and customer data exposure."
        if severity in ["High", "Critical"] else
        "Moderate exposure. Minor vulnerability remediation needed; low operational impact."
        if severity == "Medium" else
        "Low exposure. Standard risk profile with typical perimeter boundaries."
    )

    procurement_impact = (
        "Execute rigorous security clauses, verify SOC2 Type II compliance, and mandate 90-day pen testing."
        if severity in ["High", "Critical"] else
        "Require continuous security feed monitoring and SOC2 certifications."
        if severity == "Medium" else
        "No major procurement blockers. Standard security reviews apply."
    )

    # Generate AI summary in thread
    prompt = f"""
    You are an enterprise cybersecurity risk intelligence agent.
    Draft an executive summary of the cybersecurity posture of {company_name} ({domain}) based on the following findings:
    {findings}
    
    Summarize in 2-3 sentences. Identify if there are severe risks.
    """
    ai_summary = await asyncio.to_thread(generate_ai_text, prompt)

    return {
        "risk_category": "Cybersecurity",
        "risk_score": risk_score,
        "severity": severity,
        "confidence_score": 85 if references else 50,
        "findings": findings,
        "references": references[:5],
        "recommendations": [
            "Mandate SOC2 Type II certifications for all operational domains.",
            "Conduct active vulnerability scanning and patch management remediation.",
            "Implement multi-factor authentication (MFA) and data encryption policies."
        ],
        "business_impact": business_impact,
        "procurement_impact": procurement_impact,
        "ai_summary": ai_summary
    }