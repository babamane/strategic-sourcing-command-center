"""
Pricing Insights Tool
Returns pricing insights using Tavily search agent with custom prompt
"""
from langchain.tools import tool
from agents.tavily_search_agent import create_pricing_insights_agent
import json


@tool
def get_pricing_insights(company: str) -> str:
    """
    Get comprehensive pricing insights for a company using Tavily web search.
    
    This tool uses an AI agent with Tavily search to find recent pricing changes,
    announcements, and market intelligence.
    
    Args:
        company: Name of the company (e.g., "Microsoft", "Apple")
        
    Returns:
        JSON string with 'content' and 'sources' fields
    """
    try:
        # Create agent with pricing insights prompt
        agent = create_pricing_insights_agent()
        
        # Invoke agent with company name
        result = agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": f"Provide pricing insights for {company}"
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
        
        response_text = response_text.strip()
        
        # Clean markdown code block markers
        import re
        cleaned = re.sub(r'^```json\s*', '', response_text, flags=re.IGNORECASE | re.MULTILINE)
        cleaned = re.sub(r'^```\s*', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        cleaned = cleaned.strip()

        # Try to parse the entire response as a structured JSON object
        try:
            parsed_json = json.loads(cleaned)
            if isinstance(parsed_json, dict) and "content" in parsed_json:
                return json.dumps({
                    "content": parsed_json.get("content", ""),
                    "sources": parsed_json.get("sources", [])
                })
        except Exception:
            pass

        # If it doesn't parse directly as a JSON dict, fall back to older parsing rules
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
        print(f"Error in get_pricing_insights: {error_trace}")
        
        return json.dumps({
            "content": f"""**Pricing Insights**

**Status:** Unable to retrieve real-time pricing data.

**Error:** {str(e)}

**Note:** Please ensure Tavily API key is configured correctly in your .env file.

**Fallback Information:**
For the most accurate and up-to-date pricing information, please visit:
- Official {company} pricing page
- Recent press releases and investor relations updates
- Industry analyst reports""",
            "sources": []
        })
