"""
Products and Features Tool
Returns product and feature insights using Tavily search agent with custom prompt
"""
from langchain.tools import tool
from agents.tavily_search_agent import create_products_features_agent
import json


@tool
def get_products_features(company: str) -> str:
    """
    Get comprehensive product and feature insights for a company using Tavily web search.
    
    This tool uses an AI agent with Tavily search to find recent product launches,
    deprecations, and regulatory risks.
    
    Args:
        company: Name of the company (e.g., "Microsoft", "Apple")
        
    Returns:
        JSON string with 'content' and 'sources' fields
    """
    try:
        # Create agent with product features prompt
        agent = create_products_features_agent()
        
        # Invoke agent with company name
        result = agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": f"Provide product and feature insights for {company}"
                }
            ]
        })
        
        # Extract the response
        response_text = ""
        if isinstance(result, dict) and "messages" in result:
            messages = result["messages"]
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    response_text = last_message.content
                elif isinstance(last_message, dict):
                    response_text = last_message.get('content', str(last_message))
        else:
            response_text = str(result)
        
        # Parse the response to separate content and sources
        if "---SOURCES---" in response_text:
            parts = response_text.split("---SOURCES---")
            content = parts[0].strip()
            sources_text = parts[1].strip() if len(parts) > 1 else "[]"
            
            # Try to parse sources as JSON
            try:
                sources = json.loads(sources_text)
            except json.JSONDecodeError:
                # If parsing fails, return empty sources
                sources = []
        else:
            # No sources separator found, return all as content
            content = response_text
            sources = []
        
        # Return structured JSON
        return json.dumps({
            "content": content,
            "sources": sources
        })
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in get_products_features: {error_trace}")
        
        return json.dumps({
            "content": f"""**Products & Features**

**Status:** Unable to retrieve real-time product data.

**Error:** {str(e)}

**Note:** Please ensure Tavily API key is configured correctly in your .env file.

**Fallback Information:**
For the most accurate and up-to-date product information, please visit:
- Official {company} product announcements
- Recent press releases and investor relations updates
- SEC filings (10-Q, 10-K) for regulatory disclosures""",
            "sources": []
        })
