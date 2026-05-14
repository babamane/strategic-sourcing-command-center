from langchain.agents import create_agent
from utils.llm_client import LLMClient
from tools.rag_tool import RAGTool

# 1. Initialize Tools
rag_tool = RAGTool()
tools = [rag_tool]

# 2. Get LLM
llm = LLMClient().get_llm()

# 3. Create System Prompt
system_prompt = """You are a specialized RAG (Retrieval Augmented Generation) agent.
Your ONLY job is to search the local knowledge base for information about companies.

Instructions:
- Use the 'knowledge_base_search' tool to find answers.
- CRITICAL: Keep responses to EXACTLY 2-3 lines maximum (excluding the Source line).
- Summarize VERY concisely - focus only on the most essential key numbers and facts.
- Avoid long lists, bullet points, or verbose explanations.
- If you CANNOT find the answer in the knowledge base, explicitly state: "I could not find this information in the internal documents."
- Do NOT attempt to search the internet.
- Do NOT use inline citations like "(File.pdf, p.1)".
- At the VERY END of your response, on a new line, add: "Source: [filename] (Page [number])".
- Knowledge base is grounded on 10-q documents.
"""

# 4. Create Agent
rag_agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt,
)
