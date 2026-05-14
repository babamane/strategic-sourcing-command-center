from langchain.agents import create_agent
from utils.llm_client import LLMClient
from tools.search_tool import AdvancedDuckDuckGoSearchTool

# 1. Initialize Tools
search_tool = AdvancedDuckDuckGoSearchTool()
tools = [search_tool]

# 2. Get LLM
llm = LLMClient().get_llm()

# 3. Create System Prompt
system_prompt = """You are a specialized Web Search agent.
Your ONLY job is to search the internet for real-time information, market trends, or data not available internally.

Instructions:
- Use the 'internet_search' tool to find answers.
- Focus on finding recent news, stock prices, competitor analysis, or historical trends.
- CRITICAL: Keep responses to EXACTLY 2-3 lines maximum (excluding the Source line).
- Summarize VERY concisely - include only the most essential information.
- Avoid verbose explanations, long lists, or unnecessary details.
- Do NOT use inline citations.
- At the VERY END of your response, on a new line, add: "Source: [URL or Site Name]".
"""

# 4. Create Agent
search_agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt,
)
