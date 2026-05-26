import sys
from pathlib import Path
import json

# Add project root to path for imports
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agents.earning_summary_agent import get_earnings_data

def test_earnings_metrics(company_name):
    print(f"\n--- Testing Earnings Metrics for: {company_name} ---")
    try:
        data = get_earnings_data(company_name)
        # Pretty print the metrics part
        metrics = {k: v for k, v in data.items() if k != 'summary'}
        print(f"Metrics: {json.dumps(metrics, indent=2)}")
        print(f"Summary (first 200 chars): {data.get('summary', '')[:200]}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test with Apple, Google, and Microsoft
    test_earnings_metrics("Apple")
    test_earnings_metrics("Google")
    test_earnings_metrics("Microsoft")
    test_earnings_metrics("Salesforce")
