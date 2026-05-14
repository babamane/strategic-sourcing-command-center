"""
QBR Agent
Handles fetching and formatting QBR (Quarterly Business Review) reports
"""
from tools.qbr_tool import get_qbr_report


def get_qbr_data(company_name: str) -> dict:
    """
    Get QBR report for a company
    
    Args:
        company_name: Name of the company
        
    Returns:
        dict with QBR report content
    """
    content = get_qbr_report.invoke({"company": company_name})
    return {
        "content": content,
        "report_type": "qbr"
    }
