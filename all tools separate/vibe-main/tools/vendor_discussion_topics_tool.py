"""
Vendor Discussion Topics Tool
Returns vendor discussion topics and priority areas for companies
"""
from langchain.tools import tool


@tool
def get_vendor_discussion_topics(company: str) -> str:
    """
    Get vendor discussion topics and priority areas for engaging with a company's leadership.
    
    Args:
        company: Name of the company (e.g., "Microsoft", "Apple")
        
    Returns:
        Vendor discussion topics as formatted text
    """
    company_lower = company.lower()
    
    if company_lower == "microsoft":
        return """**Vendor Discussion Topics - Microsoft**

These are priority areas to raise with Microsoft leadership, with brief reasons explaining why each topic matters to you as a customer.

**AI Adoption Roadmap and Enterprise Readiness**
- Recent reporting shows slower-than-expected enterprise adoption of some Microsoft AI products. Clarifying Microsoft's roadmap, customer support model, and integration playbook is crucial.
- Helps you understand where Microsoft is investing to reduce deployment friction, and whether your own adoption timeline should adjust.
- Ensures transparency on expected ROI, especially as Microsoft refines Copilot packaging and quotas internally.

**Pricing Stability and Packaging Strategy**
- Microsoft's filings and press coverage indicate increasing cloud infrastructure costs and ongoing experimentation with AI pricing models.
- You should ask about anticipated pricing adjustments, usage-based billing shifts, and multi-year protection options.
- Important for budget predictability, especially when scaling AI, cloud, or productivity workloads.

**Product Lifecycle Visibility (Deprecations, SKUs, Feature Changes)**
- Recent quarters showed no major deprecations, but Microsoft is actively evolving Copilot, Copilot Studio, and AI-enhanced SKUs.
- Request early visibility into upcoming product changes to avoid downstream disruptions to your roadmap.
- Ensures your teams are not surprised by changes in APIs, feature availability, or support timelines.

**Cloud Reliability, Performance, and Cost Efficiency**
- SEC filings highlight ongoing cloud cost pressures and infrastructure expansion, which may affect performance or pricing.
- Important to validate Microsoft's commitments around uptime, latency, and regional availability, especially if your workloads are scaling.
- Opens opportunities to negotiate credits, reserved capacity, or workload optimization programs.

**Data Governance, Security, and Compliance for AI Workloads**
- As AI features embed deeper into Microsoft 365, Azure, and developer tools, governance and auditability are critical.
- You should press for clarity on how Microsoft handles data boundaries, fine-tuning policies, logs, retention, and tenant isolation.
- Vital for managing regulatory and customer trust impacts as AI-driven workflows expand.

**Joint Innovation and Co-Development Opportunities**
- Microsoft's strategy emphasizes embedding AI across industries — strong customers often shape product direction.
- Exploring co-innovation programs, engineering hours, or design partnerships can accelerate your roadmap.
- Important to ensure your company gets the maximum strategic value from Microsoft beyond simple licensing."""
    
    else:
        return f"Vendor discussion topics not available for {company}."
