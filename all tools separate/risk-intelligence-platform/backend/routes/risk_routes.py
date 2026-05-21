from fastapi import APIRouter
import requests
from models.vendor_model import VendorRequest
from orchestrator.risk_orchestrator import run_risk_analysis

router = APIRouter()

def resolve_domain_and_ticker(company_name: str) -> tuple[str, str]:
    """
    Dynamically guesses the company domain and fetches its ticker from Yahoo Finance search.
    """
    # Safe domain guess
    clean_name = "".join(c for c in company_name.lower() if c.isalnum())
    domain = f"{clean_name}.com"
    ticker = ""

    # Yahoo Finance Search API to find matching symbol
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={company_name}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            quotes = data.get("quotes", [])
            # Prioritize equity quotes
            equity_quotes = [q for q in quotes if q.get("quoteType") == "EQUITY"]
            if equity_quotes:
                ticker = equity_quotes[0].get("symbol", "")
            elif quotes:
                ticker = quotes[0].get("symbol", "")
    except Exception:
        pass

    # If no ticker found, default back to name upper as a fallback or leave empty
    if not ticker:
        ticker = company_name.upper().split()[0]
        
    return domain, ticker


@router.post("/analyze")
async def analyze_vendor(vendor: VendorRequest):
    # Resolve domain/ticker if empty
    domain = vendor.domain
    ticker = vendor.ticker

    if not domain or not ticker:
        resolved_domain, resolved_ticker = resolve_domain_and_ticker(vendor.company_name)
        if not domain:
            domain = resolved_domain
        if not ticker:
            ticker = resolved_ticker

    vendor_data = {
        "company_name": vendor.company_name,
        "services": vendor.services,
        "domain": domain,
        "ticker": ticker
    }

    analysis = await run_risk_analysis(vendor_data)

    return {
        "status": "success",
        "vendor": vendor_data,
        "overall_assessment": analysis["overall_assessment"],
        "heatmap": analysis["heatmap"],
        "portfolio_metrics": analysis["portfolio_metrics"],
        "alerts": analysis["alerts"],
        "benchmark": analysis["benchmark"],
        "timeline": analysis["timeline"],
        "executive_summary": analysis["executive_summary"],
        "mitigation_plan": analysis["mitigation_plan"],
        "results": analysis["results"]
    }