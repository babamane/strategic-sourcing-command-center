import logging
from langchain.agents import create_agent
from langchain.tools import tool
from utils.llm_client import LLMClient
from agents.rag_agent import rag_agent
from agents.search_agent import search_agent

# Import dashboard data sources
from agents.earning_summary_agent import get_earnings_data
from agents.highlights_agent import (
    get_pricing_insights_data,
    get_products_features_data,
    get_ai_cloud_productivity_data,
    get_vendor_discussion_topics_data
)
from agents.qbr_agent import get_qbr_data
from agents.briefing_agent import get_briefing_data
from main import fetch_stock_data, fetch_company_metrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. Define Tools to Call Sub-Agents and Data Functions

@tool("rag_search", description="Use this tool to search internal documents/knowledge base. Input should be a specific question about the company's earnings, financials, or transcripts.")
def call_rag_agent(query: str):
    """Delegates the query to the RAG Agent."""
    try:
        logger.info(f"Orchestrator calling RAG Agent with query: {query}")
        result = rag_agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })
        return result["messages"][-1].content
    except Exception as e:
        logger.error(f"RAG Agent failed: {e}")
        return f"Error querying knowledge base: {str(e)}"

@tool("web_search", description="Use this tool to search the internet. Input should be a query for real-time info, historical trends, competitor data, or anything NOT in the internal docs.")
def call_search_agent(query: str):
    """Delegates the query to the Search Agent."""
    try:
        logger.info(f"Orchestrator calling Search Agent with query: {query}")
        result = search_agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })
        return result["messages"][-1].content
    except Exception as e:
        logger.error(f"Search Agent failed: {e}")
        return f"Error searching internet: {str(e)}"

@tool("get_earnings_info", description="Get earnings summary and financial metrics (EPS, Revenue) for a company. Input: company name.")
def get_earnings_info(company_name: str):
    try:
        data = get_earnings_data(company_name)
        return str(data)
    except Exception as e:
        return f"Error fetching earnings: {str(e)}"

@tool("get_dashboard_highlights", description="Get AI-generated highlights for specific topics: 'pricing_insights', 'products_features', 'ai_cloud_productivity', or 'vendor_topics'. Input: JSON with 'company_name' and 'topic'.")
def get_dashboard_highlights(input_json: str):
    import json
    try:
        # Handle cases where input might be a flat string instead of JSON (common in LLM calls)
        if input_json.startswith("{"):
            args = json.loads(input_json)
        else:
            # Fallback for simple company name if topic is implied or provided via other means
            # but usually it should be JSON
            return "Please provide both 'company_name' and 'topic' in JSON format."
            
        company = args.get("company_name")
        topic = args.get("topic")
        
        if topic == "pricing_insights":
            return str(get_pricing_insights_data(company))
        elif topic == "products_features":
            return str(get_products_features_data(company))
        elif topic == "ai_cloud_productivity":
            return str(get_ai_cloud_productivity_data(company))
        elif topic == "vendor_topics":
            return str(get_vendor_discussion_topics_data(company))
        else:
            return "Invalid topic. Choose from: pricing_insights, products_features, ai_cloud_productivity, vendor_topics."
    except Exception as e:
        return f"Error fetching highlights: {str(e)}"

@tool("get_qbr_report", description="Get the full Quarterly Business Review (QBR) report for a company. Input: company name.")
def get_qbr_report_tool(company_name: str):
    try:
        return str(get_qbr_data(company_name))
    except Exception as e:
        return f"Error fetching QBR: {str(e)}"

@tool("get_briefing_document", description="Get the Vendor Briefing Document (context, risks, asks) for a company. Input: company name.")
def get_briefing_document_tool(company_name: str):
    try:
        return str(get_briefing_data(company_name))
    except Exception as e:
        return f"Error fetching briefing doc: {str(e)}"

@tool("get_stock_and_metrics", description="Get real-time stock price and key company metrics (Market Cap, P/E, EPS, etc.). Input: company name or ticker symbol.")
def get_stock_and_metrics_tool(company_name: str):
    try:
        stock = fetch_stock_data(company_name)
        metrics = fetch_company_metrics(company_name)
        return f"Stock: {stock.model_dump()}\nMetrics: {metrics.model_dump()}"
    except Exception as e:
        return f"Error fetching company data: {str(e)}"

# 2. Initialize Orchestrator Tools
tools = [
    call_rag_agent, 
    call_search_agent, 
    get_earnings_info, 
    get_dashboard_highlights, 
    get_qbr_report_tool, 
    get_briefing_document_tool, 
    get_stock_and_metrics_tool
]

# 3. Get LLM
llm = LLMClient().get_llm()

# 4. Create Orchestrator System Prompt
system_prompt = """You are the Lead Orchestrator for the Tier0 Vendor Briefing Assistant.
Your job is to answer user questions using the appropriate specialized tools. 
The user is looking at a dashboard with various sections, and you should use the tools to provide information consistent with that dashboard.

AVAILABLE TOOLS:
1. 'get_stock_and_metrics': Use for questions about real-time stock price, market cap, P/E ratio, dividend yield, etc. (Side Panels). Supports company names or tickers (e.g. "CSCO").
2. 'get_earnings_info': Use for questions about earnings results, recent revenue beats/misses, and the general earnings summary narrative. (Earnings Tab)
3. 'get_dashboard_highlights': Use for questions about specific dashboard topics like "Pricing Insights", "Products and Features", "AI/Cloud Trend", or "Vendor Topics". (Highlights Tab)
4. 'get_qbr_report': Use when the user specifically mentions or asks for the Quarterly Business Review. (Quarterly Business Review Tab)
5. 'get_briefing_document': Use when the user asks for the vendor briefing, risks, or strategic asks. (Briefing Tab)
6. 'rag_search': For general questions about internal documents not covered by specific dashboard tools. 
7. 'web_search': For real-time news, competitor data, or external info not in the current reports.

STRATEGY:
- If a question is about data shown on the dashboard (stock, earnings, highlights, QBR, briefing), ALWAYS use the specialized tool first.
- Analyze if the tool returns structured data or narrative, then summarize it concisely.
- For stock info, include the current price and a key metric like Market Cap.
- If the user's question is general or about the transcript details not found in structured tabs, try 'rag_search'.
- If all internal tools fail or the info is external, use 'web_search'.

FORMATTING:
- Keep responses to EXACTLY 2-3 lines maximum (excluding the Source line).
- Be extremely concise - focus only on the most essential information.
- Ensure the last line is strictly "Source: [Source Name]". Do not add anything after it.
Example Source: "Source: Earnings Dashboard", "Source: Microsoft Q1 10-Q", "Source: Google Finance".
"""

# 5. Create Orchestrator Agent
chatbot_agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt,
)

logger.info("Orchestrator Chatbot Agent with Dashboard Tools initialized successfully.")
