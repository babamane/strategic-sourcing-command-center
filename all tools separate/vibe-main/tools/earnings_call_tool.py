from langchain.tools import tool
from earningscall import get_company
import logging
import traceback

logger = logging.getLogger(__name__)

@tool("fetch_latest_transcript")
def fetch_latest_transcript(ticker: str):
    """
    Fetches the text of the latest earnings call transcript for a given company ticker (e.g., 'AAPL', 'META', 'MSFT').
    Returns the year, quarter, and the full transcript text.
    """
    try:
        print(f"TOOL DEBUG: Fetching transcript for ticker: {ticker}")
        company = get_company(ticker)
        events = company.events()
        
        if not events:
            print("TOOL DEBUG: No events found")
            return "No earnings events found for this company."
        
        # Get latest event
        latest = events[0]
        print(f"TOOL DEBUG: Found latest event: {latest.year} Q{latest.quarter}")
        
        transcript = company.get_transcript(event=latest)
        
        if not transcript:
            print("TOOL DEBUG: No transcript found")
            return f"No transcript text available for {latest.year} Q{latest.quarter}."
        
        print(f"TOOL DEBUG: Transcript fetched successfully. Length: {len(transcript.text)}")
        
        import json
        result = {
            "ticker": ticker,
            "year": latest.year,
            "quarter": latest.quarter,
            "content": transcript.text
        }
        return json.dumps(result)
        
    except Exception as e:
        print(f"TOOL DEBUG: Error: {e}")
        traceback.print_exc()
        return f"Error fetching transcript: {str(e)}"
