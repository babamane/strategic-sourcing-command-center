import sys
from pathlib import Path

# Add project root to path for imports
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from main import fetch_stock_data, fetch_company_metrics

def test_metrics(company):
    print(f"\n--- Testing {company} ---")
    try:
        stock = fetch_stock_data(company)
        print(f"Stock Data: {stock}")
    except Exception as e:
        print(f"Stock Data Error: {e}")
        
    try:
        metrics = fetch_company_metrics(company)
        print(f"Company Metrics: {metrics}")
    except Exception as e:
        print(f"Company Metrics Error: {e}")

if __name__ == "__main__":
    test_metrics("Juniper")
    test_metrics("JNPR")
    test_metrics("Cisco")
    test_metrics("CSCO")
