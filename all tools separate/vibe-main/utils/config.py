import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)

class Config:
    """Global configuration settings"""
    # API Keys
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    LLAMA_API_KEY = os.getenv('LLAMA_API_KEY')
    
    # Provider + Models
    LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'google')  # google | openai | llama | ollama
    
    # Default model for Google (Gemini)
    GOOGLE_LLM_MODEL = os.getenv('GOOGLE_LLM_MODEL', 'gemini-2.0-flash-exp')
    
    # Provider-specific models
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    LLAMA_MODEL = os.getenv('LLAMA_MODEL', 'llama-3.3')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama-3.1')
    
    DEFAULT_TEMPERATURE = float(os.getenv('TEMPERATURE', '0.3'))
 
    # for ollama
    OLLAMA_LOCAL_HOST = os.getenv('OLLAMA_LOCAL_HOST', 'http://localhost:11434')
    
    # Agent Settings
    MAX_ITERATIONS = int(os.getenv('MAX_ITERATIONS', '10'))
    VERBOSE = os.getenv('VERBOSE', 'True').lower() == 'true'
    
    # Summarization Settings
    # Options: 'fast' (single-shot 500k limit) or 'map_reduce' (hierarchical)
    SUMMARY_METHOD = os.getenv('SUMMARY_METHOD', 'fast')
    
    # Tavily API Key
    TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
    
    # Paths
    BASE_DIR = Path(__file__).parent.parent
    PROMPTS_DIR = BASE_DIR / 'prompts'
    TOOLS_DIR = BASE_DIR / 'tools'
    OUTPUT_DIR = BASE_DIR / os.getenv('OUTPUT_DIR', 'summaries')
    
    @classmethod
    def validate(cls):
        """Validate critical configuration"""
        if cls.LLM_PROVIDER == 'google' and not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is missing in .env file")
        if cls.LLM_PROVIDER == 'openai' and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is missing in .env file")
        if cls.LLM_PROVIDER == 'llama' and not cls.LLAMA_API_KEY:
            raise ValueError("LLAMA_API_KEY is missing in .env file")
        if cls.LLM_PROVIDER == 'ollama' and not cls.OLLAMA_LOCAL_HOST:
            raise ValueError("OLLAMA_LOCAL_HOST is missing in .env file")
        if not cls.TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY is missing in .env file")

# Ensure output directory exists
os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
