import sys
from pathlib import Path

# Add project root to path for imports
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from main import resolve_symbol

def test_resolve(input_str):
    try:
        symbol = resolve_symbol(input_str)
        print(f"Input: '{input_str}' -> Resolved Symbol: {symbol}")
    except Exception as e:
        print(f"Input: '{input_str}' -> Error: {e}")

if __name__ == "__main__":
    test_resolve("Cisco")
    test_resolve("CSCO")
    test_resolve("Microsoft")
    test_resolve("MSFT")
    test_resolve("Apple")
    test_resolve("AAPL")
    test_resolve("UnknownCompany")
