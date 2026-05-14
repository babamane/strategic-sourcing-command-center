"""
Briefing Docs Tool
Generates briefing documents for companies
"""
from langchain.tools import tool


@tool
def get_briefing_doc(company: str) -> str:
    """
    Generate a briefing document for a company meeting.
    
    Args:
        company: Name of the company (e.g., "Microsoft", "Apple")
        
    Returns:
        Briefing document as formatted text
    """
    company_lower = company.lower()
    
    if company_lower == "microsoft":
        return """**Briefing Document - Microsoft**

**Purpose of This Brief**
This page equips you with the latest context on Microsoft's performance, product direction, pricing behavior, and AI/cloud strategy — and highlights the exact questions and negotiation angles to use in the meeting. It is designed to help you steer the discussion, validate Microsoft's commitments, and secure clearer alignment for our roadmap.

**Current State of Microsoft (What You Should Know Before the Meeting)**
- Microsoft is performing strongly overall, with Azure remaining the central growth engine. AI services contributed, but enterprise adoption is slower than Microsoft initially projected.
- Because of this slower AI scaling, Microsoft is refining pricing, packaging and deployment support for Copilot and Azure AI — making this a key moment for us to negotiate clarity and cost predictability.
- Cloud infrastructure investment is rising; this may influence pricing and support structures in coming quarters.
- No major product deprecations were announced recently, but Microsoft is actively adjusting AI feature sets and enterprise SKUs based on feedback.
- Microsoft is pushing harder on customer "AI readiness," meaning we may see new deployment requirements, integration steps, or program changes.

**Why This Matters for Us**
- Pricing uncertainty for AI and cloud workloads could impact our annual and multi-year budgeting if not negotiated proactively.
- Changes in Copilot, Azure AI, data governance policies, or SKUs may affect upcoming projects and integrations.
- Slower enterprise AI adoption means Microsoft is looking to prove customer success — an opportunity for us to secure more support, credits, or co-innovation.
- Microsoft's push for deeper AI adoption aligns with our roadmap, but only if governance, security and cost frameworks are locked down in advance.

**Priority Discussion Topics (What You Should Bring Up)**
- **AI Adoption Roadmap:** Ask for Microsoft's concrete deployment pathway, adoption benchmarks, and what "done right" looks like in the next 12–18 months.
- **Pricing & Packaging Stability:** Request multi-year predictability and clarity on AI, Copilot, and Azure consumption pricing, especially given the internal adjustments Microsoft is making.
- **Product & Feature Visibility:** Push for early notice on upcoming changes to AI features, SKUs, APIs, or integration requirements.
- **Cloud Reliability & Cost Efficiency:** Align on uptime, failover, cost-optimization measures, and opportunities for workload credits or reserved pricing.
- **Data Governance & Compliance for AI:** Validate data boundaries, tenant isolation, retention, and auditability — especially critical as we expand regulated workloads.
- **Co-Innovation Opportunities:** Identify areas where Microsoft can provide engineering hours, early access, or pilot programs to accelerate our initiatives.

**CEO-Level "Asks" to Have Ready**
- A commitment for pricing protection for AI and cloud services for the next 2–3 years.
- A named Microsoft executive sponsor for our enterprise AI transformation.
- Priority access to Copilot enhancements, tooling, and architectural support.
- A joint success plan with measurable milestones and quarterly check-ins.
- Clear documentation and advance notice for any changes that affect our roadmap.

**Red Flags / Watch Areas**
- AI adoption friction persists — meaning Microsoft may push aggressive incentives; we should leverage this.
- AI pricing evolution is still fluid; we must lock terms now.
- Changes in support structures and product bundles can create hidden operational cost."""
    
    else:
        return f"Briefing document not available for {company}."
