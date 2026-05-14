"""
Earning Summary Agent
Handles fetching earnings transcripts and generating summaries with metrics
"""
import json
from langchain_core.messages import HumanMessage
from utils.llm_client import LLMClient
from tools.earnings_call_tool import fetch_latest_transcript


# Ticker mapping based on frontend/src/data/companies.js
TICKER_MAP = {
    "Meta": "META",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Google": "GOOGL",
    "Salesforce": "CRM",
    "Adobe": "ADBE",
    "Cisco": "CSCO",
    "Juniper": "JNPR",
    "Cognizant": "CTSH",
    "Wipro": "WIT"
}


def get_earnings_data(company_name: str) -> dict:
    """
    Fetch earnings data for a company
    
    Args:
        company_name: Name of the company (e.g., "Microsoft", "Apple")
        
    Returns:
        dict with earnings metrics and summary
    """
    ticker = TICKER_MAP.get(company_name, company_name.upper())
    print(f"DEBUG: Fetching earnings for {company_name} -> Ticker: {ticker}")

    # 1. Manually fetch transcript
    print(f"DEBUG: Invoking tool manually for {ticker}")
    tool_output = fetch_latest_transcript.invoke({"ticker": ticker})
    
    # Parse JSON output
    try:
        transcript_data = json.loads(tool_output)
        transcript_text = transcript_data.get("content", "")
        year = transcript_data.get("year", "Unknown")
        quarter = transcript_data.get("quarter", "Unknown")
        print(f"DEBUG: Parsed Transcript: {year} Q{quarter}, Length: {len(transcript_text)}")
    except json.JSONDecodeError:
        print(f"DEBUG: Failed to parse JSON, using raw output")
        transcript_text = tool_output
        year = "Unknown"
        quarter = "Unknown"

    # 2. Generate Summary (Dynamic for ALL companies)
    llm = LLMClient().get_llm()
    
    summary_prompt = f"""You are an expert financial analyst.
Analyze the following earnings call transcript for {company_name} ({year} Q{quarter}).

TRANSCRIPT START:
{transcript_text[:60000]}
TRANSCRIPT END

Generate a comprehensive "Earnings Overview" (400-500 words).
- Use bullet points for key takeaways.
- Highlight revenue drivers, strategic updates, and future guidance.
- Make it professional and easy to read.
- Do NOT include the raw metrics table in the summary, just the narrative.
"""
    summary_response = llm.invoke([HumanMessage(content=summary_prompt)])
    generated_summary = summary_response.content

    # 3. Get Metrics (Hardcoded for Microsoft, can be extended for others)
    metrics = {}
    
    if company_name.lower() == "microsoft":
        metrics = {
            "announce_date": "2025-10-29",
            "eps_estimated": "$3.67",
            "eps_actual": "$4.15",
            "eps_surprise_percent": "Beat by 12.5%",
            "revenue_actual": "$77.67B",
            "revenue_surprise": "Beat by $2.18B"
        }
    else:
        # For other companies, return placeholder metrics
        # TODO: Implement dynamic metric extraction for other companies
        metrics = {
            "announce_date": "Not Available",
            "eps_estimated": "Not Available",
            "eps_actual": "Not Available",
            "eps_surprise_percent": "Not Available",
            "revenue_actual": "Not Available",
            "revenue_surprise": "Not Available"
        }

    # Return combined result
    return {
        **metrics,
        "summary": generated_summary
    }
