import sys
from pathlib import Path

# Add project root to path for imports
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agents.chatbot_agent import chatbot_agent

def test_ticker_query(query):
    print(f"\n--- Testing Ticker Query: '{query}' ---")
    try:
        response = chatbot_agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })
        final_message = response["messages"][-1]
        print(f"Bot: {final_message.content}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test specific ticker CSCO as requested by user
    test_ticker_query("what is the current stock price of CSCO?")
    # Test another ticker
    test_ticker_query("How is MSFT doing today?")
