"""
Briefing Agent
Handles fetching and formatting briefing documents
"""
from tools.briefing_tool import get_briefing_doc


def get_briefing_data(company_name: str) -> dict:
    """
    Get briefing document for a company
    
    Args:
        company_name: Name of the company
        
    Returns:
        dict with briefing document content
    """
    content = get_briefing_doc.invoke({"company": company_name})
    return {
        "content": content,
        "doc_type": "briefing"
    }
