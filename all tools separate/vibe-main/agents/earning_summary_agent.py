"""
Earning Summary Agent 
Handles fetching earnings transcripts and generating summaries with metrics
"""
import json
import yfinance as yf
from langchain_core.messages import HumanMessage
from utils.llm_client import LLMClient
from tools.earnings_call_tool import fetch_latest_transcript
from tools.tavily_search_tool import TavilySearchTool


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

def format_number(val, is_currency=True):
    """Helper to format large numbers to B/T notation"""
    if val is None or val == "Not Available":
        return "Not Available"
    try:
        prefix = "$" if is_currency else ""
        num = float(val)
        if abs(num) >= 1e12:
            return f"{prefix}{num/1e12:.2f}T"
        elif abs(num) >= 1e9:
            return f"{prefix}{num/1e9:.2f}B"
        elif abs(num) >= 1e6:
            return f"{prefix}{num/1e6:.2f}M"
        else:
            return f"{prefix}{num:.2f}"
    except:
        return str(val)


def _is_usable_source_text(text: str) -> bool:
    lowered = (text or "").strip().lower()
    if len(lowered) < 300:
        return False
    failure_markers = [
        "error fetching transcript",
        "no transcript",
        "unable to access",
        "unable to retrieve",
        "proxyerror",
        "connection refused",
    ]
    return not any(marker in lowered for marker in failure_markers)


def _fetch_live_earnings_context(company_name: str, ticker: str) -> tuple[str, str, str, list]:
    tool_output = fetch_latest_transcript.invoke({"ticker": ticker})
    transcript_text = ""
    year = "Unknown"
    quarter = "Unknown"
    sources = []

    try:
        transcript_data = json.loads(tool_output)
        transcript_text = transcript_data.get("content", "")
        year = transcript_data.get("year", "Unknown")
        quarter = transcript_data.get("quarter", "Unknown")
        if _is_usable_source_text(transcript_text):
            sources.append({
                "title": f"{company_name} earnings call transcript",
                "url": "https://earningscall.biz",
                "date": f"{year} Q{quarter}",
            })
            return transcript_text, year, quarter, sources
    except json.JSONDecodeError:
        transcript_text = tool_output

    if _is_usable_source_text(transcript_text):
        return transcript_text, year, quarter, sources

    query = (
        f"{company_name} latest quarterly earnings results revenue EPS cloud AI "
        "investor relations earnings release"
    )
    search_result = TavilySearchTool.invoke({"query": query})
    search_text = json.dumps(search_result, default=str)
    if not _is_usable_source_text(search_text):
        raise RuntimeError("Live earnings sources were unavailable.")

    results = search_result.get("results", []) if isinstance(search_result, dict) else []
    for item in results[:5]:
        sources.append({
            "title": item.get("title", "Live earnings source"),
            "url": item.get("url", ""),
            "date": item.get("published_date", ""),
        })

    year = "Latest"
    quarter = "Quarter"
    return search_text, year, quarter, sources

def get_earnings_data(company_name: str) -> dict:
    """
    Fetch earnings data for a company using yfinance for metrics and LLM for summary
    """
    ticker = TICKER_MAP.get(company_name, company_name.upper())
    print(f"DEBUG: Fetching earnings for {company_name} -> Ticker: {ticker}")

    # 1. Fetch Basic Metrics via yfinance (Reliable Source)
    metrics = {
        "announce_date": "Not Available",
        "eps_estimated": "Not Available",
        "eps_actual": "Not Available",
        "eps_surprise_percent": "Not Available",
        "revenue_actual": "Not Available",
        "revenue_surprise": "Not Available"
    }
    
    try:
        yf_ticker = yf.Ticker(ticker)
        info = yf_ticker.info
        
        # Get EPS metrics
        try:
            earning_dates = yf_ticker.earnings_dates
            if earning_dates is not None and not earning_dates.empty:
                # Filter for reported EPS to get the latest ACTUAL result
                reported = earning_dates[earning_dates['Reported EPS'].notnull()]
                if not reported.empty:
                    latest = reported.iloc[0]
                    metrics["announce_date"] = reported.index[0].strftime("%Y-%m-%d")
                    metrics["eps_estimated"] = f"${latest['EPS Estimate']:.2f}" if latest['EPS Estimate'] else "Not Available"
                    metrics["eps_actual"] = f"${latest['Reported EPS']:.2f}" if latest['Reported EPS'] else "Not Available"
                    
                    surprise = latest['Surprise(%)']
                    if surprise is not None:
                        label = "Beat" if surprise > 0 else "Missed"
                        metrics["eps_surprise_percent"] = f"{label} by {abs(surprise):.1f}%"
        except Exception as e:
            print(f"DEBUG: Error fetching yf earnings_dates: {e}")

        # Get Revenue
        rev = info.get('totalRevenue')
        if rev:
            metrics["revenue_actual"] = format_number(rev)
            
        # Revenue surprise is harder to get from yfinance directly, we'll try to get it from transcript if available
    except Exception as e:
        print(f"DEBUG: yfinance metrics failed: {e}")

    # 2. Fetch transcript first, then Tavily as a live web fallback.
    transcript_text, year, quarter, sources = _fetch_live_earnings_context(company_name, ticker)

    # 3. Generate Summary and optionally extract missing metrics via LLM
    llm = LLMClient().get_llm()

    # Prompt for both summary and metric enhancement
    prompt = f"""You are an expert financial analyst.
Analyze the following earnings call transcript (or use general knowledge if unavailable) for {company_name} ({year} Q{quarter}).

TRANSCRIPT START:
{transcript_text[:60000]}
TRANSCRIPT END

    TASK:
    1. Generate a comprehensive "Earnings Overview" (300-400 words) with bullet points.
    2. Extract these specific metrics if you find them:
       - Revenue Surprise (e.g., "Beat by $2.1B" or "Missed by 1%")
       - Any metrics currently missing from our data: {json.dumps(metrics)}

    Return your response in this JSON format:
    {{
      "summary": "Full narrative summary here...",
      "metrics": {{
        "revenue_surprise": "extracted value or Not Available",
        "eps_estimated": "only if Not Available previously",
        ...
      }}
    }}
    """
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        # Clean response
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        parsed = json.loads(content)
        generated_summary = parsed.get("summary", "Summary generation failed.")
        
        # Merge extracted metrics if they are better than what we have
        extracted_metrics = parsed.get("metrics", {})
        for key, val in extracted_metrics.items():
            if metrics.get(key) == "Not Available" and val != "Not Available":
                metrics[key] = val
                
    except Exception as e:
        print(f"DEBUG: LLM summary/extraction failed: {e}")
        raise RuntimeError(f"Live LLM earnings summary failed: {e}") from e

    return {
        **metrics,
        "summary": generated_summary,
        "sources": sources,
        "live": True
    }
