"""
QBR (Quarterly Business Review) Tool
Generates QBR reports for companies
"""
from langchain.tools import tool


@tool
def get_qbr_report(company: str) -> str:
    """
    Generate a Quarterly Business Review (QBR) report for a company.
    
    Args:
        company: Name of the company (e.g., "Microsoft", "Apple")
        
    Returns:
        QBR report as formatted text
    """
    company_lower = company.lower()
    
    if company_lower == "microsoft":
        return """**Quarterly Business Review - Microsoft**

**Business Performance Overview**
- Microsoft delivered strong, broad-based performance in FY26 Q1 with continued momentum across Cloud, AI, and Productivity segments.
- Azure remained the primary driver of revenue growth as enterprises expanded cloud workloads and infrastructure modernization programs.
- Microsoft 365 and Windows OEM showed steady demand, while Gaming and Xbox content also contributed positively to quarterly results.
- Management emphasized that AI is embedded across the product portfolio, but enterprise adoption patterns remain uneven, requiring ongoing customer education and deployment support.

**Key Financial Highlights**
- Intelligent Cloud was the standout segment, benefiting from Azure consumption growth and increased enterprise workloads.
- Higher cloud infrastructure investment continues to pressure gross margins but supports long-term capacity for AI and hyperscale demand.
- Commercial cloud revenue grew meaningfully year-over-year, supported by Microsoft 365, Dynamics, and Azure AI services.
- Cost controls and efficiency measures helped offset infrastructure spending, enabling strong overall operating income performance.

**AI, Cloud, and Product Priorities**
- Expansion of Copilot features across Microsoft 365, Power Platform, Dynamics, and Windows remains a central strategy.
- Microsoft is aligning its go-to-market around AI-driven transformation scenarios, helping customers operationalize AI beyond pilots.
- The company is refining enterprise packaging for AI services after slower-than-expected adoption in some areas, focusing on clearer value realization and easier integration paths.
- Azure continues to scale foundational AI infrastructure, positioning Microsoft as a leading cloud provider for training, inference, and industry-specific AI models.

**Market and Customer Insights**
- Enterprises are increasing cloud investments but remain cautious on large-scale AI rollouts until ROI and integration costs are clearer.
- Longer deployment cycles for advanced AI products have led Microsoft to focus more on solution architecture, migration tooling, and customer enablement programs.
- Public sector and regulated industries show growing interest in secure AI deployments, driving demand for governance and compliance capabilities built into Microsoft Cloud.

**Key Risks and Watch Areas**
- Rising cloud infrastructure spend may continue to affect margins as Microsoft scales data centers for AI.
- Competitive pressure in cloud and AI markets remains high, requiring sustained innovation and pricing discipline.
- Execution risk around enterprise AI adoption persists if customers delay large-scale deployments.

**Strategic Outlook**
- Microsoft projects continued strength across cloud workloads and steady adoption of AI-assisted productivity tools.
- Leadership signals sustained investment in AI infrastructure, developer tools, and enterprise integration frameworks.
- The focus for the coming quarters is helping customers convert AI vision into operational value, improving time-to-adoption and lowering integration friction."""
    
    else:
        return f"QBR report not available for {company}."
