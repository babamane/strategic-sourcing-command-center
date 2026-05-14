"""
Meta Spend and Metrics Tool
Returns Meta spend and metrics information for companies
"""
from langchain.tools import tool


@tool
def get_meta_spend_metrics(company: str) -> str:
    """
    Get Meta spend and metrics information including spend summary and service SLAs.
    
    Args:
        company: Name of the company (e.g., "Microsoft", "Apple")
        
    Returns:
        Meta spend and metrics data as formatted text
    """
    company_lower = company.lower()
    
    if company_lower == "microsoft":
        return """**Meta Spend and Metrics - Microsoft**

**Meta Spend Summary:**
*This section will be populated once we integrate with Meta's data.*

**Service SLAs:**
*This section will be populated once we integrate with Meta's data.*

**Performance Metrics:**
*This section will be populated once we integrate with Meta's data.*

**Integration Status:**
⚠️ This feature requires integration with Meta's data platform. Coming soon."""
    
    else:
        return f"""**Meta Spend and Metrics - {company}**

**Meta Spend Summary:**
*This section will be populated once we integrate with Meta's data.*

**Service SLAs:**
*This section will be populated once we integrate with Meta's data.*

**Performance Metrics:**
*This section will be populated once we integrate with Meta's data.*

**Integration Status:**
⚠️ This feature requires integration with Meta's data platform. Coming soon."""
