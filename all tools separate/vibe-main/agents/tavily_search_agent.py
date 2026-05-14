"""
Tavily Search Agent
Creates agents that use Tavily search tool with custom prompts from files
"""
from langchain.agents import create_agent
from utils.llm_client import LLMClient
from tools.tavily_search_tool import TavilySearchTool
from utils.config import Config
from pathlib import Path


def load_prompt_from_file(prompt_filename: str) -> str:
    """
    Load a prompt from the prompts directory.
    
    Args:
        prompt_filename: Name of the prompt file (e.g., 'price_insight_prompt.txt')
        
    Returns:
        Prompt content as string
    """
    prompt_path = Config.PROMPTS_DIR / prompt_filename
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()


def create_tavily_agent(prompt_filename: str):
    """
    Create an agent that uses Tavily search with a custom prompt from file.
    
    Args:
        prompt_filename: Name of the prompt file in the prompts directory
        
    Returns:
        Configured LangChain agent
    """
    # Initialize Tavily search tool (it's already an instance, not a class)
    tavily_tool = TavilySearchTool
    tools = [tavily_tool]
    
    # Get LLM
    llm = LLMClient().get_llm()
    
    # Load prompt from file
    system_prompt = load_prompt_from_file(prompt_filename)
    
    # Create agent
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
    )
    
    return agent


# Pre-configured agents for different use cases
def create_pricing_insights_agent():
    """Create agent for pricing insights using price_insight_prompt.txt"""
    return create_tavily_agent("price_insight_prompt.txt")


def create_products_features_agent():
    """Create agent for products/features using product_features_prompt.txt"""
    return create_tavily_agent("product_features_prompt.txt")


def create_ai_cloud_productivity_agent():
    """Create agent for AI/cloud/productivity using ai_cloud_productivity_prompt.txt"""
    return create_tavily_agent("ai_cloud_productivity_prompt.txt")
