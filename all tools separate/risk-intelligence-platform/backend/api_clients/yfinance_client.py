import yfinance as yf


def fetch_company_financials(ticker_symbol):

    try:

        company = yf.Ticker(ticker_symbol)

        info = company.info

        financial_data = {
            "company_name": info.get("longName"),
            "market_cap": info.get("marketCap"),
            "revenue": info.get("totalRevenue"),
            "profit_margin": info.get("profitMargins"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "current_price": info.get("currentPrice"),
            "recommendation": info.get("recommendationKey"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
        }

        return financial_data

    except Exception as e:

        return {"error": str(e)}
