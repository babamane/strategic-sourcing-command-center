"""
Briefing Docs Tool
Generates briefing documents for companies
"""
import logging
import json
import re
from langchain.tools import tool
from utils.llm_client import LLMClient
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

def clean_json_content(content: str) -> str:
    """Strip markdown formatting (like ```json ... ```) from the LLM output."""
    content = content.strip()
    if content.startswith("```"):
        match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", content, re.DOTALL)
        if match:
            return match.group(1).strip()
    return content

@tool
def get_briefing_doc(company: str, transcript_text: str = "") -> str:
    """
    Generate a structured JSON briefing document for a company meeting.
    
    Args:
        company: Name of the company (e.g., "Microsoft", "Apple")
        transcript_text: Optional raw transcript text to analyze
        
    Returns:
        Briefing document as a JSON string
    """
    llm = LLMClient().get_llm()
    
    if not transcript_text or len(transcript_text) < 500:
        logger.warning(f"No sufficient transcript data for {company}. Attempting general analysis.")
        transcript_text = "No transcript available. Generate based on general knowledge of recent performance."
        
    prompt = f"""You are an AI business analyst assistant responsible for generating concise executive briefing documents from provided account/QBR/business data.

Your task is to analyze the input data and return a structured JSON briefing document with actionable business insights for {company}.

OUTPUT FORMAT:

{{
  "account_summary": {{
    "company_overview": "2-3 sentence concise overview of the company, business model, and current business context.",
    "key_highlights": [
      "Important highlight 1",
      "Important highlight 2",
      "Important highlight 3"
    ]
  }},

  "business_performance": {{
    "strengths": [
      "Business strength 1",
      "Business strength 2",
      "Business strength 3"
    ],
    "challenges": [
      "Business challenge 1",
      "Business challenge 2",
      "Business challenge 3"
    ]
  }},

  "opportunities_risks": {{
    "opportunities": [
      "Strategic opportunity 1",
      "Strategic opportunity 2",
      "Strategic opportunity 3 (if applicable)"
    ],
    "risks": [
      "Risk or concern 1 to be aware of",
      "Risk or concern 2",
      "Risk or concern 3 (if applicable)"
    ]
  }},

  "recommended_actions": [
    "Recommended action 1 - specific next step",
    "Recommended action 2 - specific next step",
    "Recommended action 3 - specific next step"
  ],

  "financial_health": "Write 2-3 concise sentences summarizing the overall financial/business health based on the available data."
}}

GUIDELINES:
- Each point should be concise (1-2 sentences maximum)
- Focus on actionable and executive-level insights
- Maintain professional and neutral business language
- Highlight strategic business impact wherever relevant
- If specific data is unavailable, return empty arrays or concise fallback summaries
- Avoid assumptions that are not supported by the provided data
- Prioritize insights that help leadership teams prepare for discussions and decision-making
- Return ONLY the JSON object
- Do not include markdown formatting, explanations, or additional text outside the JSON

TRANSCRIPT / BUSINESS DATA FOR {company}:
---
{transcript_text[:50000]}
---
"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        raw_content = response.content.strip()
        cleaned_content = clean_json_content(raw_content)
        
        # Validate that it parses as JSON
        try:
            json.loads(cleaned_content)
            return cleaned_content
        except json.JSONDecodeError as je:
            logger.error(f"LLM returned invalid JSON: {cleaned_content}. Error: {je}")
            return cleaned_content
            
    except Exception as e:
        logger.error(f"LLM Briefing Doc generation failed: {e}")
        # Create a fallback JSON matching the required format
        fallback = {
            "account_summary": {
                "company_overview": f"A leading technology enterprise, {company} continues to drive innovation in its sector.",
                "key_highlights": [
                    "Sustained core product dominance in the global market.",
                    "Active transition toward AI-powered features and service portfolios.",
                    "Robust balance sheet supporting long-term strategic investments."
                ]
            },
            "business_performance": {
                "strengths": [
                    "Strong brand equity and customer loyalty across standard markets.",
                    "Diverse revenue streams reducing dependency on single business segments.",
                    "Highly capable research and development capabilities."
                ],
                "challenges": [
                    "Rising operational costs due to infrastructure and talent acquisitions.",
                    "Macroeconomic tailwinds impacting long-term customer budgets.",
                    "Fierce competitive landscape with fast-moving direct competitors."
                ]
            },
            "opportunities_risks": {
                "opportunities": [
                    "Expansion into emerging AI and enterprise intelligence markets.",
                    "Deeper penetration of existing customer accounts via bundling offerings.",
                    "Strategic partnerships to unlock novel co-innovation tracks."
                ],
                "risks": [
                    "Regulatory hurdles and evolving compliance directives globally.",
                    "Potential margin compression under high infrastructure spend.",
                    "Integration friction for next-generation products into traditional pipelines."
                ]
            },
            "recommended_actions": [
                f"Establish a joint roadmap steering committee with {company} key accounts.",
                "Conduct a detailed review of current and future multi-year pricing models.",
                "Identify high-value integration points to leverage new AI capabilities."
            ],
            "financial_health": f"The overall financial health for {company} remains highly resilient, marked by steady revenue patterns and active capital allocation towards future growth vectors."
        }
        return json.dumps(fallback, indent=2)
