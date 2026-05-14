from langchain_tavily import TavilySearch
from utils.config import Config


# Initialize the Tavily search instance - this is already a LangChain tool
# Optimized settings to prevent context length exceeded errors
tavily_search = TavilySearch(
    api_key=Config.TAVILY_API_KEY,
    max_results=5,                  # Reduced from 10 to limit token usage
    topic="general",                # pricing, earnings, licensing
    search_depth="advanced",        # Deep crawl for comprehensive results
    include_raw_content=False,      # Disabled to prevent massive token usage (main fix)
    include_answer=True             # Tavily generates a combined answer (most important)
)

# Export as TavilySearchTool for backward compatibility
TavilySearchTool = tavily_search
