import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

load_dotenv()
from utils.llm_client import LLMClient

COMPANIES = ["adobe", "cisco", "cognizant", "google", "juniper", "microsoft", "salesforce", "wipro"]

PROMPT = """You are a financial analyst. Based on the provided old earnings JSON and company name, generate a structured JSON matching this exact schema:
{{"content": "your markdown content", "sources": [{{"title": "", "url": "", "date": ""}}]}}

Check if {company} publishes public earnings:
- Public companies: Use official quarterly earnings reports
- Private companies: Acknowledge this upfront

FORMAT the content EXACTLY like this:

## Overview
- Just provide a 3-4 sentence summary: revenue ($XXB, up XX% YoY), EPS ($X.XX vs estimate), key segment performance, and main theme of the quarter.

## Key Takeaways
- Revenue/growth milestone with specific numbers (e.g., "$XXB, XX% growth")
- Growth driver with metrics (e.g., "XX% YoY, driven by...")
- Segment performance with revenue and growth rate
- Product adoption metric (e.g., "XX% of Fortune 500 using...")
- Forward indicator (e.g., "RPO reached $XXB, up XX%")

## Highlights
- CapEx or infrastructure investment with $ amount
- Technology achievement with specific metric
- Customer/product milestone with numbers
- Strategic initiative with measurable outcome
- Geographic or market expansion detail

## Investment Focus Areas
- Products: List key products company is investing in
- AI & Cloud: Specific $ amounts, infrastructure, partnerships
- Strategic Priorities: Main focus areas and market positioning

RULES:
1. Use ## for headers, - for bullets
2. No bold (**) in body text except Investment Focus labels
3. Include SPECIFIC numbers: $, %, users, dates
4. Maximum 400 words
5. Use official investor relations sources or realistic mock sources in the sources array.
6. Return ONLY valid JSON, do not include ```json markdown blocks.

Company: {company}
Old Data Context:
{old_data}
"""

def main():
    llm = LLMClient().get_llm()
    
    for company in COMPANIES:
        print(f"Migrating earnings for {company}...")
        mock_path = project_root / "mock_data" / company / "earnings.json"
        
        old_data = ""
        if mock_path.exists():
            try:
                with open(mock_path, "r", encoding="utf-8") as f:
                    old_data = f.read()
            except Exception as e:
                print(f"  Error reading {mock_path}: {e}")
        else:
            old_data = "No prior data found. Generate based on general knowledge."
            
        formatted_prompt = PROMPT.format(company=company.capitalize(), old_data=old_data)
        
        try:
            response = llm.invoke([HumanMessage(content=formatted_prompt)])
            content = response.content.strip()
            
            # Clean markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
                
            # Verify it's valid JSON
            parsed = json.loads(content)
            if "content" not in parsed:
                raise ValueError("Missing 'content' key")
                
            with open(mock_path, "w", encoding="utf-8") as f:
                json.dump(parsed, f, indent=4)
                
            print(f"  Successfully migrated {company}")
        except Exception as e:
            print(f"  Failed migrating {company}: {e}")

if __name__ == "__main__":
    main()
