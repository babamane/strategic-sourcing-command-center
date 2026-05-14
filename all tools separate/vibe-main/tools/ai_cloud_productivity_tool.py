"""
AI, Cloud and Productivity Tool
Returns AI, cloud, and productivity insights for companies
"""
from langchain.tools import tool


@tool
def get_ai_cloud_productivity(company: str) -> str:
    """
    Get AI, cloud, and productivity insights for a company.
    
    Args:
        company: Name of the company (e.g., "Microsoft", "Apple")
        
    Returns:
        AI, cloud, and productivity data as formatted text
    """
    company_lower = company.lower()
    
    if company_lower == "microsoft":
        return """**AI, Cloud & Productivity - Microsoft**

**Azure growth:** 
Azure and Intelligent Cloud remain the primary growth engine — Azure revenue growth drove sequential segment gains in FY26 Q1 (Oct 29, 2025 release).

**AI adoption reality check:** 
Multiple outlets (Dec 2025) reported Microsoft dialing back internal AI sales quotas for some offerings after slower enterprise conversion; this highlights a gap between capability launches and enterprise integration at scale. Expect increased emphasis on data integration, professional services, and usage-based pricing to close that gap.

**Productivity stack:** 
Microsoft 365 commercial cloud revenue continues to expand; Microsoft is emphasizing embedding Copilot features across productivity apps while iterating on enterprise-grade controls for data governance."""
    
    else:
        return f"AI, cloud, and productivity data not available for {company}."
