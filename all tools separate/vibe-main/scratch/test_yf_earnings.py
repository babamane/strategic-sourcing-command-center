import yfinance as yf
import json

def test_yf_earnings(ticker_symbol):
    print(f"--- Testing {ticker_symbol} ---")
    ticker = yf.Ticker(ticker_symbol)
    
    # Try getting earnings dates
    try:
        print("Earnings Dates:")
        print(ticker.earnings_dates)
    except Exception as e:
        print(f"Error getting earnings dates: {e}")
        
    # Try getting info metrics
    try:
        print("\nInfo Metrics:")
        info = ticker.info
        print(f"Trailing EPS: {info.get('trailingEps')}")
        print(f"Forward EPS: {info.get('forwardEps')}")
        print(f"Total Revenue: {info.get('totalRevenue')}")
    except Exception as e:
        print(f"Error getting info: {e}")

if __name__ == "__main__":
    test_yf_earnings("MSFT")
    test_yf_earnings("AAPL")
    test_yf_earnings("GOOGL")
