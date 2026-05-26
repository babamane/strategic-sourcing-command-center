from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import yfinance as yf
from pathlib import Path
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
# ------------ Config ------------ #

PERIODS = ["5d", "1mo", "6mo", "1y", "5y", "10y"]


# ------------ Pydantic models: stock data ------------ #

class StockCandle(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class StockDataResponse(BaseModel):
    company_name: str
    symbol: str
    realtime_price: Optional[float] = None
    currency: Optional[str] = None
    exchange: Optional[str] = None
    historical_data: Dict[str, List[StockCandle]]


class StockRequest(BaseModel):
    company_name: str = Field(..., description="Company name, e.g. 'Microsoft' or 'Apple'.")


# ------------ Pydantic models: company metrics ------------ #

class CompanyMetricsRequest(BaseModel):
    company_name: str = Field(..., description="Company name, e.g. 'Microsoft' or 'Apple'.")


class CompanyMetricsResponse(BaseModel):
    company_name: str
    symbol: str
    market_cap: Optional[str] = None      # e.g. "3.61T"
    beta: Optional[float] = None
    pe_ratio: Optional[float] = None
    eps: Optional[float] = None
    dividend: Optional[float] = None
    dividend_yield: Optional[str] = None  # e.g. "0.70%"
    next_earnings_date: Optional[str] = None  # ISO date string if possible


# ------------ FastAPI app ------------ #

app = FastAPI(title="Stock Data & Metrics API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------ Helper: resolve company name → ticker ------------ #

def resolve_symbol(company_name: str) -> str:
    """
    Resolve company name to stock ticker symbol.

    Replace with your own mapping / DB / external API as needed.
    """
    mapping = {
        "microsoft": "MSFT",
        "google": "GOOGL",
        "alphabet": "GOOGL",
        "salesforce": "CRM",
        "adobe": "ADBE",
        "cisco": "CSCO",
        "juniper": "JNPR",
        "cognizant": "CTSH",
        "wipro": "WIT",
        # Legacy mappings
        "apple": "AAPL",
        "amazon": "AMZN",
        "meta": "META",
        "facebook": "META",
        "tesla": "TSLA",
    }

    key = company_name.strip().lower()
    symbol = mapping.get(key)

    # If not found in mapping, check if it's already a symbol (e.g. "CSCO")
    if not symbol:
        # If it's all caps and 1-5 chars, treat it as a symbol
        if company_name.isupper() and 1 <= len(company_name) <= 5:
            return company_name
        # Fallback: check if the uppercase version is in the values of the mapping
        if company_name.upper() in mapping.values():
            return company_name.upper()
            
        raise ValueError(f"Unknown company name or ticker '{company_name}'. Please map it to a ticker symbol.")

    return symbol


# ------------ Core: yfinance stock data (periods) ------------ #

def fetch_stock_data(company_name: str) -> StockDataResponse:
    # 1. Resolve company name → ticker
    try:
        symbol = resolve_symbol(company_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    ticker = yf.Ticker(symbol)

    # 2. Realtime price
    info = getattr(ticker, "info", {}) or {}
    realtime_price = info.get("currentPrice") or info.get("regularMarketPrice")

    if realtime_price is None:
        price_hist = ticker.history(period="1d")
        realtime_price = float(price_hist["Close"].iloc[-1]) if not price_hist.empty else None

    # 3. Info
    info = getattr(ticker, "info", {}) or {}
    currency = info.get("currency")
    exchange = info.get("exchange")

    # 4. Historical OHLCV for required periods
    historical_data: Dict[str, List[StockCandle]] = {}

    for period in PERIODS:
        hist = ticker.history(period=period, interval="1d")
        if hist.empty:
            historical_data[period] = []
            continue

        hist = hist.reset_index()

        candles: List[StockCandle] = []
        for _, row in hist.iterrows():
            date_col = "Date" if "Date" in row.index else "Datetime"
            date_str = row[date_col].strftime("%Y-%m-%d")

            candles.append(
                StockCandle(
                    date=date_str,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row["Volume"]),
                )
            )

        historical_data[period] = candles

    return StockDataResponse(
        company_name=company_name,
        symbol=symbol,
        realtime_price=realtime_price,
        currency=currency,
        exchange=exchange,
        historical_data=historical_data,
    )


# ------------ Core: yfinance company metrics (no LLM) ------------ #

def format_market_cap(market_cap: Optional[int]) -> Optional[str]:
    """
    Convert raw integer market cap into human-readable string like '3.61T', '350B', etc.
    """
    if market_cap is None:
        return None

    trillion = 1_000_000_000_000
    billion = 1_000_000_000
    million = 1_000_000

    if market_cap >= trillion:
        return f"{market_cap / trillion:.2f}T"
    elif market_cap >= billion:
        return f"{market_cap / billion:.2f}B"
    elif market_cap >= million:
        return f"{market_cap / million:.2f}M"
    else:
        return str(market_cap)


def fetch_company_metrics(company_name: str) -> CompanyMetricsResponse:
    try:
        symbol = resolve_symbol(company_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    ticker = yf.Ticker(symbol)
    info = getattr(ticker, "info", {}) or {}

    # Market cap
    raw_market_cap = info.get("marketCap")
    market_cap = format_market_cap(raw_market_cap) if raw_market_cap is not None else None

    # Beta
    beta = info.get("beta")

    # P/E (use trailingPE if available, else forwardPE)
    pe_ratio = info.get("trailingPE") or info.get("forwardPE")

    # EPS (trailingEps preferred)
    eps = info.get("trailingEps") or info.get("forwardEps")

    # Dividend and yield
    dividend = info.get("dividendRate")
    raw_yield = info.get("dividendYield")  # typically a fraction, e.g. 0.007
    dividend_yield = f"{raw_yield * 100:.2f}%" if isinstance(raw_yield, (int, float)) else None

    # Next earnings date
    next_earnings_date: Optional[str] = None
    try:
        # yfinance has get_earnings_dates in newer versions
        earnings_dates = ticker.get_earnings_dates(limit=1)
        if earnings_dates is not None and not earnings_dates.empty:
            # index is DatetimeIndex
            next_earnings_date = earnings_dates.index[0].date().isoformat()
    except Exception:
        # Fallback: some info dicts have 'earningsTimestamp' or similar
        ts = info.get("earningsTimestamp")
        if ts:
            from datetime import datetime

            try:
                next_earnings_date = datetime.fromtimestamp(ts).date().isoformat()
            except Exception:
                next_earnings_date = None

    return CompanyMetricsResponse(
        company_name=company_name,
        symbol=symbol,
        market_cap=market_cap,
        beta=beta,
        pe_ratio=pe_ratio,
        eps=eps,
        dividend=dividend,
        dividend_yield=dividend_yield,
        next_earnings_date=next_earnings_date,
    )


# ------------ Endpoints ------------ #

@app.post("/stock-data", response_model=StockDataResponse)
def get_stock_data(request: StockRequest):
    """
    Returns realtime price + historical OHLCV data for:
    5d, 1mo, 6mo, 1y, 5y, 10y

    Input: company_name (e.g. "Microsoft")
    """
    return fetch_stock_data(request.company_name)


@app.post("/company-metrics", response_model=CompanyMetricsResponse)
def get_company_metrics(request: CompanyMetricsRequest):
    """
    Returns key company metrics (no LLM):

    - Market Cap (formatted, e.g. "3.61T")
    - Beta
    - P/E
    - EPS
    - Dividend
    - Dividend Yield (e.g. "0.70%")
    - Next Earnings Date (YYYY-MM-DD if available)
    """
    return fetch_company_metrics(request.company_name)

@app.get("/", response_class=HTMLResponse)
def serve_index():
    return Path("index.html").read_text(encoding="utf-8")