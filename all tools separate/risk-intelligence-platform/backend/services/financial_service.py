import asyncio
from api_clients.yfinance_client import fetch_company_financials

def fetch_financial_data(ticker: str) -> dict:
    """
    Fetches financial details for a given ticker from Yahoo Finance.
    """
    if not ticker:
        return {"error": "No ticker symbol provided"}
    return fetch_company_financials(ticker)

async def analyze_financial_risk_service(vendor_data: dict) -> dict:
    """
    Helper service to analyze financial risk of a vendor.
    Runs yfinance client call in a background thread to prevent event loop blocking.
    """
    ticker = vendor_data.get("ticker", "")
    financial_data = await asyncio.to_thread(fetch_financial_data, ticker)

    findings = []
    risk_score = 0

    if "error" in financial_data:
        findings.append(f"Financial retrieval error: {financial_data['error']}")
        risk_score += 30
        return {
            "risk_score": risk_score,
            "financial_data": {},
            "findings": findings
        }

    if financial_data.get("market_cap"):
        findings.append(f"Market Capitalization: ${financial_data['market_cap']:,}")
    else:
        findings.append("Market Cap data unavailable")
        risk_score += 10

    profit_margin = financial_data.get("profit_margin")
    if profit_margin is not None:
        findings.append(f"Profit Margin: {profit_margin * 100:.2f}%")
        if profit_margin < 0:
            findings.append("Negative profitability detected (operating at a loss)")
            risk_score += 35
        elif profit_margin < 0.05:
            findings.append("Low profitability detected (margin below 5%)")
            risk_score += 15
    else:
        findings.append("Profit margin data unavailable")
        risk_score += 10

    debt_to_equity = financial_data.get("debt_to_equity")
    if debt_to_equity is not None:
        findings.append(f"Debt-to-Equity Ratio: {debt_to_equity:.2f}")
        if debt_to_equity > 150:
            findings.append("High leverage detected (debt-to-equity > 150)")
            risk_score += 20
    else:
        findings.append("Debt-to-equity ratio unavailable")

    current_ratio = financial_data.get("current_ratio")
    if current_ratio is not None:
        findings.append(f"Current Ratio: {current_ratio:.2f}")
        if current_ratio < 1.0:
            findings.append("Liquidity concern: Current ratio is below 1.0")
            risk_score += 15
    else:
        findings.append("Current liquidity ratio unavailable")

    return {
        "risk_score": min(risk_score, 100),
        "financial_data": financial_data,
        "findings": findings
    }