import logging
import json
from tools.qbr_tool import get_qbr_report
from tools.earnings_call_tool import fetch_latest_transcript
from main import resolve_symbol

logger = logging.getLogger(__name__)

def get_qbr_data(company_name: str) -> dict:
    """
    Generate a dynamic QBR report for a company by fetching the latest transcript.
    
    Args:
        company_name: Name of the company
        
    Returns:
        dict with QBR report content
    """
    try:
        # 1. Resolve company name to ticker
        ticker = resolve_symbol(company_name)
        logger.info(f"Generating QBR for {company_name} (Ticker: {ticker})")
        
        # 2. Fetch transcript text
        transcript_data_raw = fetch_latest_transcript.invoke({"ticker": ticker})
        transcript_text = ""
        
        try:
            transcript_json = json.loads(transcript_data_raw)
            transcript_text = transcript_json.get("content", "")
        except:
            # Fallback if it's already a string or format is unexpected
            transcript_text = transcript_data_raw

        # 3. Call QBR report generator tool (now dynamic)
        content = get_qbr_report.invoke({
            "company": company_name,
            "transcript_text": transcript_text
        })
        
        return {
            "content": content,
            "report_type": "qbr",
            "ticker": ticker
        }
    except Exception as e:
        logger.error(f"Error in get_qbr_data for {company_name}: {e}")
        return {
            "content": f"Failed to generate QBR report for {company_name}: {str(e)}",
            "report_type": "qbr",
            "error": True
        }
