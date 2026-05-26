from langchain.tools import tool
from agents.tavily_search_agent import create_ai_cloud_productivity_agent
import json


@tool
def get_ai_cloud_productivity(company: str) -> str:
    """
    Get AI, cloud, and productivity insights for a company.
    
    This tool uses an AI agent with Tavily search to find recent cloud performance,
    AI adoption strategies, and infrastructure updates.
    
    Args:
        company: Name of the company (e.g., "Microsoft", "Apple")
        
    Returns:
        JSON string with 'content' and 'sources' fields
    """
    try:
        # Create agent with ai cloud productivity prompt
        agent = create_ai_cloud_productivity_agent()
        
        # Invoke agent with company name
        result = agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": f"Provide AI, cloud and productivity insights for {company}"
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
        print(f"Error in get_ai_cloud_productivity: {error_trace}")
        
        return json.dumps({
            "content": f"**AI, Cloud & Productivity - {company}**\n\n**Status:** Unable to retrieve real-time data.\n\n**Error:** {str(e)}",
            "sources": []
        })
