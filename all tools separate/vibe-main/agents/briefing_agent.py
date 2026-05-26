"""
Briefing Agent
Handles fetching and formatting briefing documents
"""
import logging
import json
from tools.briefing_tool import get_briefing_doc
from tools.earnings_call_tool import fetch_latest_transcript
from main import resolve_symbol

logger = logging.getLogger(__name__)


def get_briefing_data(company_name: str) -> dict:
    """
    Get briefing document for a company
    
    Args:
        company_name: Name of the company
        
    Returns:
        dict with briefing document content
    """
    try:
        # 1. Resolve company name to ticker symbol
        ticker = resolve_symbol(company_name)
        logger.info(f"Generating Briefing for {company_name} (Ticker: {ticker})")
        
        # 2. Fetch transcript text
        transcript_data_raw = fetch_latest_transcript.invoke({"ticker": ticker})
        transcript_text = ""
        
        try:
            transcript_json = json.loads(transcript_data_raw)
            transcript_text = transcript_json.get("content", "")
        except Exception:
            # Fallback if transcript raw data is just a string
            transcript_text = transcript_data_raw
            
        # 3. Call briefing generator tool with transcript
        content = get_briefing_doc.invoke({
            "company": company_name,
            "transcript_text": transcript_text
        })
        
        return {
            "content": content,
            "doc_type": "briefing"
        }
    except Exception as e:
        logger.error(f"Error in get_briefing_data for {company_name}: {e}")
        # Fallback to get_briefing_doc without transcript
        content = get_briefing_doc.invoke({"company": company_name})
        return {
            "content": content,
            "doc_type": "briefing"
        }
