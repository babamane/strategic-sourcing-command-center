from langchain.tools import tool
from utils.llm_client import LLMClient
from langchain_core.messages import HumanMessage
import logging

logger = logging.getLogger(__name__)

@tool
def get_qbr_report(company: str, transcript_text: str = "") -> str:
    """
    Generate a Quarterly Business Review (QBR) report for a company.
    If transcript_text is provided, uses LLM to generate a dynamic report.
    
    Args:
        company: Name of the company
        transcript_text: Optional raw transcript text to analyze
        
    Returns:
        QBR report as formatted text
    """
    llm = LLMClient().get_llm()
    
    # If no transcript is provided, we might still try to generate something general or use search
    # but the current architecture expects the agent to fetch the transcript.
    if not transcript_text or len(transcript_text) < 500:
        logger.warning(f"No sufficient transcript data for {company}. Attempting general summary.")
        transcript_text = "No transcript available. Generate based on general knowledge of recent performance."

    prompt = f"""You are a senior business analyst. Your task is to generate a comprehensive "Quarterly Business Review (QBR)" report for {company} based on the provided earnings call transcript.

THE REPORT MUST FOLLOW THIS EXACT STRUCTURE AND STYLE:

**Quarterly Business Review - [Company Name]**

**Business Performance Overview**
- [3-4 bullet points about general performance, segment growth, and momentum]

**Key Financial Highlights**
- [3-4 bullet points about revenue, margins, specific segment standouts, and efficiency]

**AI, Cloud, and Product Priorities**
- [3-4 bullet points about AI strategy, cloud infrastructure, and core product updates]

**Market and Customer Insights**
- [3-4 bullet points about customer adoption, ROI concerns, and market sentiment]

**Key Risks and Watch Areas**
- [3-4 bullet points about competitive pressure, infrastructure costs, and execution risks]

**Strategic Outlook**
- [2-3 bullet points about future guidance, investment focus, and long-term vision]

---
TRANSCRIPT DATA:
{transcript_text[:50000]}  # Limit to 50k chars to stay within context limits
---

Instructions:
1. Be professional, analytical, and data-driven.
2. Use the provided transcript as the primary source of truth.
3. Keep the bullet points concise but informative.
4. Ensure the output is valid Markdown.
5. Do not include any preamble or conversational text, only the report.
"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        report_content = response.content.strip()
        return report_content
    except Exception as e:
        logger.error(f"LLM QBR generation failed: {e}")
        return f"Error generating QBR report for {company}: {str(e)}"
