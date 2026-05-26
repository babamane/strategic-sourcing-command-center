from langchain.tools import tool
from agents.tavily_search_agent import create_vendor_topics_agent
import json


@tool
def get_vendor_discussion_topics(company: str) -> str:
    """
    Get vendor discussion topics and priority areas for engaging with a company's leadership.
    
    This tool uses an AI agent with Tavily search to find strategic priorities,
    roadmap updates, and innovation opportunities.
    
    Args:
        company: Name of the company (e.g., "Microsoft", "Apple")
        
    Returns:
        JSON string with 'content' and 'sources' fields
    """
    try:
        # Create agent with vendor topics prompt
        agent = create_vendor_topics_agent()
        
        # Invoke agent with company name
        result = agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": f"Provide vendor discussion topics for {company}"
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
            if isinstance(parsed_json, dict) and ("pricing_strategy" in parsed_json or "ai_cloud_integration" in parsed_json):
                return json.dumps({
                    "content": json.dumps(parsed_json),
                    "sources": []
                })
        except Exception:
            pass

        # If it doesn't parse directly as a JSON dict, fall back to older parsing rules
        content = response_text
        sources = []
        
        try:
            # Try to find JSON code block first
            json_match = re.search(r'```(?:json)?\s*(\[\s*\{.*?\}\s*\])\s*```', response_text, re.DOTALL)
            
            if json_match:
                sources_text = json_match.group(1)
                sources = json.loads(sources_text)
                content = response_text[:json_match.start()].strip()
            elif "---SOURCES---" in response_text:
                parts = response_text.split("---SOURCES---")
                content = parts[0].strip()
                sources_text = parts[1].strip() if len(parts) > 1 else "[]"
                sources_text = sources_text.replace("```json", "").replace("```", "").strip()
                sources = json.loads(sources_text)
            elif "**SOURCES:**" in response_text:
                parts = response_text.split("**SOURCES:**")
                content = parts[0].strip()
                sources_text = parts[1].strip() if len(parts) > 1 else "[]"
                sources_text = sources_text.replace("```json", "").replace("```", "").strip()
                sources = json.loads(sources_text)
            
            # Clean up trailing horizontal rules and source headers in content
            content = re.sub(r'(?i)\n*(?:\*|#|-)*\s*SOURCES\s*.*$', '', content).strip()
            content = re.sub(r'\n+---+\s*$', '', content).strip()
            
        except json.JSONDecodeError:
            # If parsing fails
            pass
        
        # Return structured JSON
        return json.dumps({
            "content": content,
            "sources": sources
        })
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in get_vendor_discussion_topics: {error_trace}")
        
        return json.dumps({
            "content": f"**Vendor Discussion Topics - {company}**\n\n**Status:** Unable to retrieve real-time topics.\n\n**Error:** {str(e)}",
            "sources": []
        })
