import sys
from pathlib import Path

# Add project root to path for imports
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from utils.llm_client import LLMClient
from utils.config import Config

def test_llm():
    print(f"Current Provider: {Config.LLM_PROVIDER}")
    print(f"Current Model: {Config.OPENAI_MODEL}")
    
    try:
        client = LLMClient()
        llm = client.get_llm()
        print("LLM initialized successfully.")
        
        # Simple invocation
        response = llm.invoke("Hello, say 'OpenAI is working' if you can hear me.")
        print(f"Response: {response.content}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_llm()
