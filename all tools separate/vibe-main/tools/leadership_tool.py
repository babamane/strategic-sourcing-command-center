"""
Leadership Tool
Returns structured executive leadership details using Tavily search agent with custom prompt
"""
from langchain.tools import tool
from agents.tavily_search_agent import create_leadership_agent
import json
import re


@tool
def get_leadership(company: str) -> str:
    """
    Get comprehensive executive leadership details for a company using Tavily web search.
    
    This tool uses an AI agent with Tavily search to find key executives, their titles,
    start years, and biographies.
    
    Args:
        company: Name of the company (e.g., "Microsoft", "Cisco")
        
    Returns:
        JSON string with 'content' and 'sources' fields
    """
    try:
        # Create agent with leadership prompt
        agent = create_leadership_agent()
        
        # Invoke agent with company name
        result = agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": f"Identify the key executive leadership members for {company}"
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
        cleaned = re.sub(r'^```json\s*', '', response_text, flags=re.IGNORECASE | re.MULTILINE)
        cleaned = re.sub(r'^```\s*', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
        cleaned = cleaned.strip()

        # Try to parse the entire response as a structured JSON object
        try:
            parsed_json = json.loads(cleaned)
            # Ensure it is a list of objects or parses correctly
            if isinstance(parsed_json, list):
                return json.dumps({
                    "content": json.dumps(parsed_json),
                    "sources": []
                })
        except Exception:
            pass

        # Return structured JSON fallback
        return json.dumps({
            "content": "[]",
            "sources": []
        })
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in get_leadership: {error_trace}")
        return json.dumps({
            "content": "[]",
            "sources": []
        })
