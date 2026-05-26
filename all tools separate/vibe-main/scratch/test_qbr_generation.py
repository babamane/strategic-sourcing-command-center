import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agents.qbr_agent import get_qbr_data
import json

def test_qbr(company):
    print(f"\n--- Testing QBR for {company} ---")
    try:
        result = get_qbr_data(company)
        if "error" in result:
            print(f"Error: {result['content']}")
        else:
            print(f"Success! Ticker: {result.get('ticker')}")
            print("Content Snippet:")
            print(result['content'][:500] + "...")
    except Exception as e:
        print(f"Unexpected Exception: {e}")

if __name__ == "__main__":
    test_companies = ["Microsoft", "Google", "Salesforce", "Cisco"]
    for company in test_companies:
        test_qbr(company)
