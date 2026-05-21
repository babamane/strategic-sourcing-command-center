import asyncio
from services.tavily_service import tavily_search
from services.llm_service import generate_ai_text, evaluate_agent_risk_score

async def analyze_compliance_risk(vendor_data: dict) -> dict:
    """
    Compliance Agent: Assesses the vendor's regulatory compliance posture, security certifications,
    GDPR compliance, HIPAA, PCI-DSS, SOC2 Type II status, and audits.
    """
    company_name = vendor_data.get("company_name", "")
    
    findings = []
    references = []
    risk_score = 0

    try:
        query = f"{company_name} SOC2 ISO 27001 compliance audit GDPR certification PCI-DSS HIPAA violation"
        response = await asyncio.to_thread(tavily_search, query)
        if response.get("results"):
            has_soc2 = False
            has_iso = False
            compliance_violation_count = 0
            
            for item in response["results"]:
                title = item.get("title", "")
                content = item.get("content", "")
                combined = (title + " " + content).lower()
                
                if "soc" in combined and "2" in combined:
                    has_soc2 = True
                if "iso" in combined and "27001" in combined:
                    has_iso = True
                
                if any(keyword in combined for keyword in ["violation", "fine", "non-compliant", "breach", "complaint", "fail"]):
                    if compliance_violation_count < 2:
                        findings.append(f"Compliance concern: {title}")
                        risk_score += 15
                        compliance_violation_count += 1
                
                references.append({
                    "title": title,
                    "url": item.get("url")
                })
            
            if has_soc2:
                findings.append("Compliance audit shows evidence of SOC 2 certification alignment.")
            else:
                findings.append("No explicit reference to SOC 2 Type II audits found. Verification recommended.")
                risk_score += 12
                
            if has_iso:
                findings.append("Compliance audit shows evidence of ISO 27001 security certification.")
            else:
                findings.append("No explicit reference to ISO 27001 security framework found.")
                risk_score += 8
                
    except Exception as e:
        findings.append(f"Compliance audit check failed: {str(e)}")
        risk_score += 20

    # Final calculations using dynamic LLM/cryptographic risk evaluation
    risk_score = evaluate_agent_risk_score("Compliance Risk", company_name, findings, risk_score)
    
    severity = "Low"
    if risk_score >= 75:
        severity = "Critical"
    elif risk_score >= 55:
        severity = "High"
    elif risk_score >= 40:
        severity = "Medium"

    business_impact = (
        "Lack of security certifications (SOC2/ISO) increases the likelihood of data breaches and potential "
        "secondary liability. GDPR/HIPAA compliance violations can lead to heavy regulatory fines."
        if severity in ["High", "Critical"] else
        "Standard compliance posture. Vendor holds essential security certs with minor compliance recommendations."
    )

    procurement_impact = (
        "Do not onboard without a formal SOC2 Type II report and GDPR compliance validation. Request remediation timeline."
        if severity in ["High", "Critical"] else
        "Standard onboarding. Request certificate copies for validation."
    )

    # Generate AI summary in thread
    prompt = f"""
    You are a regulatory compliance auditor and security certifications analyst.
    Summarize the compliance risk profile of {company_name} based on the following findings:
    {findings}
    
    Summarize in 2-3 sentences. Note if SOC2, ISO 27001, or GDPR certifications appear to be missing or violated.
    """
    ai_summary = await asyncio.to_thread(generate_ai_text, prompt)

    return {
        "risk_category": "Compliance Risk",
        "risk_score": risk_score,
        "severity": severity,
        "confidence_score": 85 if references else 50,
        "findings": findings,
        "references": references[:5],
        "recommendations": [
            "Request physical copy of current year's SOC 2 Type II report.",
            "Verify compliance certifications (ISO 27001, GDPR compliance statements).",
            "Incorporate compliance failure indemnity clauses in the contract."
        ],
        "business_impact": business_impact,
        "procurement_impact": procurement_impact,
        "ai_summary": ai_summary
    }
