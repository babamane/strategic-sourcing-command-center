import sys
from pathlib import Path

# Add project root to path for imports
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from agents.chatbot_agent import chatbot_agent

def test_query(query, company="Microsoft"):
    print(f"\n--- Testing Query: '{query}' for {company} ---")
    contextualized_input = f"For company '{company}': {query}"
    try:
        response = chatbot_agent.invoke({
            "messages": [{"role": "user", "content": contextualized_input}]
        })
        # The response structure from create_agent is usually {'messages': [...]}
        # or similar depending on how create_agent is implemented.
        # Based on chatbot_agent.py, it seems to return the LangChain agent response.
        final_message = response["messages"][-1]
        print(f"Bot: {final_message.content}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Test stock and metrics
    test_query("What is the current stock price and market cap?")
    
    # Test earnings
    test_query("Tell me about the recent earnings performance.")
    
    # Test highlights
    test_query("What are the pricing insights?")
    
    # Test QBR
    test_query("Summarize the Quarterly Business Review.")
