import logging
from langchain.agents import create_agent
from langchain.tools import tool
from utils.llm_client import LLMClient
from agents.rag_agent import rag_agent
from agents.search_agent import search_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. Define Tools to Call Sub-Agents

@tool("rag_search", description="Use this tool to search internal documents/knowledge base. Input should be a specific question about the company's earnings, financials, or transcripts.")
def call_rag_agent(query: str):
    """Delegates the query to the RAG Agent."""
    try:
        logger.info(f"Orchestrator calling RAG Agent with query: {query}")
        result = rag_agent.invoke({
            "messages": [{"role": "user", "content": query}]
        })
        # Extract the last message content
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

# 2. Initialize Orchestrator Tools
tools = [call_rag_agent, call_search_agent]

# 3. Get LLM
llm = LLMClient().get_llm()

# 4. Create Orchestrator System Prompt
system_prompt = """You are the Lead Orchestrator for the Tier0 Vendor Briefing Assistant.
Your job is to route user questions to the correct specialized agent.

You have two specialized workers:
1. 'rag_search': For questions about the specific company's earnings report, transcripts, and internal documents. (e.g., "What was the revenue?", "Summarize the call").
2. 'web_search': For questions about market trends, stock prices, competitors, or historical data not in the current report. (e.g., "Stock price today", "Price trends over 3 years").

STRATEGY:
- Analyze the user's question carefully.
- Decide which agent is best suited to answer.
- Call that agent with a clear, specific query.
- If the 'rag_search' agent returns "I could not find this information", you MUST then call the 'web_search' agent to find it externally.
- Do NOT answer the question yourself. Delegate it.

FORMATTING:
- Return the final answer from the sub-agent directly.
- CRITICAL: Keep responses to EXACTLY 2-3 lines maximum (excluding the Source line).
- Be extremely concise - focus only on the most essential information.
- Ensure the last line is strictly "Source: [Source Name]". Do not add anything after it.
"""

# 5. Create Orchestrator Agent
chatbot_agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt,
)

logger.info("Orchestrator Chatbot Agent initialized successfully.")
