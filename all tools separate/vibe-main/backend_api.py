from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings



# Add project root to path for imports
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from main import fetch_stock_data, fetch_company_metrics, StockDataResponse, CompanyMetricsResponse, StockRequest, CompanyMetricsRequest
from utils.config import Config
import json
import os

app = FastAPI(title="Earning Docs API", version="1.0.0")


def load_mock_json(company_name: str, filename: str):
    mock_path = os.path.join("mock_data", company_name.lower(), filename)
    if os.path.exists(mock_path):
        with open(mock_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_mock_text(company_name: str, filename: str):
    mock_path = os.path.join("mock_data", company_name.lower(), filename)
    if os.path.exists(mock_path):
        with open(mock_path, "r", encoding="utf-8") as f:
            return f.read()
    return None


def has_preloaded_vendor_data(company_name: str):
    return os.path.isdir(os.path.join("mock_data", company_name.lower()))


def no_preloaded_data_message(company_name: str):
    return (
        f"No preloaded dashboard data is available for {company_name} yet. "
        "Add earnings, highlights, and briefing files under mock_data for this vendor, "
        "or enable a live data generation workflow."
    )


def no_preloaded_highlight(company_name: str, tab: str):
    labels = {
        "leadership": "Leadership",
        "vendor_topics": "Vendor Discussion Topics",
        "pricing_insights": "Pricing Insights",
        "products_features": "Products and Features",
        "ai_cloud_productivity": "AI, Cloud and Productivity",
    }
    label = labels.get(tab, tab.replace("_", " ").title())
    return {
        "content": f"## {label}\n\n{no_preloaded_data_message(company_name)}",
        "sources": []
    }


def _as_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, indent=2)


def build_chatbot_context(company_name: str, message: str = ""):
    """Collect the same local data shown in the dashboard for chatbot answers."""
    company_key = company_name.lower()
    sections = []
    message_lower = message.lower()

    file_labels = {
        "earnings.json": "Earnings",
        "briefing.json": "Briefing Doc",
        "highlights_leadership.json": "Leadership",
        "highlights_vendor_topics.json": "Vendor Discussion Topics",
        "highlights_pricing_insights.json": "Pricing Insights",
        "highlights_products_features.json": "Products and Features",
        "highlights_ai_cloud_productivity.json": "AI, Cloud and Productivity",
    }

    for filename, label in file_labels.items():
        if (
            ("earning" in message_lower or "revenue" in message_lower or "highlight" in message_lower)
            and filename != "earnings.json"
        ):
            continue
        if (
            ("briefing" in message_lower or "briefing doc" in message_lower or "risk" in message_lower or "action" in message_lower)
            and filename != "briefing.json"
        ):
            continue
        if "leadership" in message_lower and filename != "highlights_leadership.json":
            continue
        if "pricing" in message_lower and filename != "highlights_pricing_insights.json":
            continue
        if ("cloud" in message_lower or "ai" in message_lower or "productivity" in message_lower) and filename != "highlights_ai_cloud_productivity.json":
            continue
        if (
            ("products and features" in message_lower or "product feature" in message_lower or "features" in message_lower)
            and filename != "highlights_products_features.json"
        ):
            continue
        if "vendor topic" in message_lower and filename != "highlights_vendor_topics.json":
            continue

        data = load_mock_json(company_key, filename)
        if not data:
            continue
        content = data.get("content", data) if isinstance(data, dict) else data
        sections.append(f"## {label}\n{_as_text(content)}")

    qbr = load_mock_text(company_key, "qbr.md")
    if qbr and ("qbr" in message_lower or "quarterly business review" in message_lower):
        sections.append(f"## QBR\n{qbr}")

    return "\n\n".join(sections)


def fallback_chatbot_answer(company_name: str, message: str, context: str):
    if not context:
        return (
            f"{no_preloaded_data_message(company_name)}\n"
            "Source: Vendor Data Status"
        )

    message_lower = message.lower()

    earnings = load_mock_json(company_name, "earnings.json") or {}
    earnings_content = earnings.get("content", "")
    highlights = []
    in_relevant_section = False
    for line in earnings_content.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_relevant_section = stripped.lower() in {"## key takeaways", "## highlights"}
            continue
        if in_relevant_section and stripped.startswith("- "):
            highlights.append(stripped[2:])
        if len(highlights) >= 3:
            break

    if "highlight" in message_lower and highlights:
        answer = "Key highlights: " + " ".join(f"{item}" for item in highlights)
    elif "briefing" in message_lower or "risk" in message_lower:
        answer = "The briefing doc includes account context, business performance, opportunities, risks, and recommended actions."
    elif "cloud" in message_lower or "ai" in message_lower or "productivity" in message_lower:
        ai_data = load_mock_json(company_name, "highlights_ai_cloud_productivity.json") or {}
        ai_content = ai_data.get("content", "")
        bullets = [line.strip()[2:] for line in ai_content.splitlines() if line.strip().startswith("- ")][:3]
        answer = "AI and productivity highlights: " + " ".join(bullets) if bullets else "The AI, Cloud, and Productivity section covers recent AI product launches, cloud momentum, productivity updates, and enterprise platform features."
    elif "earning" in message_lower or "revenue" in message_lower:
        overview = next((line.strip() for line in earnings_content.splitlines() if line.strip() and not line.startswith("#")), "")
        answer = overview or "The earnings section includes the latest available revenue, EPS, key takeaways, and investment focus areas."
    else:
        answer = "I found local dashboard data for this vendor. Ask about earnings, highlights, pricing, leadership, products, AI/cloud, or briefing risks."

    return f"{answer}\nSource: Local Dashboard Data"


def _content_for(company_name: str, filename: str):
    data = load_mock_json(company_name, filename) or {}
    return data.get("content", data) if isinstance(data, dict) else data


def _bullets_from_markdown(text: str, limit: int = 4):
    return [line.strip()[2:] for line in str(text).splitlines() if line.strip().startswith("- ")][:limit]


def _first_paragraph(text: str):
    for line in str(text).splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("- "):
            return stripped
    return ""


def answer_from_dashboard_data(company_name: str, message: str):
    message_lower = message.lower()

    if not has_preloaded_vendor_data(company_name):
        return (
            f"{no_preloaded_data_message(company_name)}\n"
            "Source: Vendor Data Status"
        )

    if any(word in message_lower for word in ["ai", "cloud", "productivity", "copilot"]):
        content = _content_for(company_name, "highlights_ai_cloud_productivity.json")
        bullets = _bullets_from_markdown(content)
        intro = _first_paragraph(content)
        answer = intro
        if bullets:
            answer += " Key items: " + " ".join(bullets[:3])
        return f"{answer}\nSource: AI, Cloud and Productivity"

    if any(word in message_lower for word in ["pricing", "price", "cost", "discount"]):
        content = _content_for(company_name, "highlights_pricing_insights.json")
        bullets = _bullets_from_markdown(content)
        answer = _first_paragraph(content) or "Pricing insights are available for this vendor."
        if bullets:
            answer += " Key pricing points: " + " ".join(bullets[:3])
        return f"{answer}\nSource: Pricing Insights"

    if any(word in message_lower for word in ["leadership", "leader", "ceo", "cfo", "executive"]):
        content = _content_for(company_name, "highlights_leadership.json")
        try:
            leaders = json.loads(content) if isinstance(content, str) else content
            if isinstance(leaders, list) and leaders:
                names = [f"{leader.get('name')} ({leader.get('title')})" for leader in leaders[:4]]
                return f"Leadership includes {', '.join(names)}.\nSource: Leadership"
        except Exception:
            pass
        return fallback_chatbot_answer(company_name, message, str(content))

    if any(word in message_lower for word in ["product", "feature", "launch", "roadmap"]):
        content = _content_for(company_name, "highlights_products_features.json")
        bullets = _bullets_from_markdown(content)
        answer = _first_paragraph(content) or "Product and feature updates are available for this vendor."
        if bullets:
            answer += " Key updates: " + " ".join(bullets[:3])
        return f"{answer}\nSource: Products and Features"

    if any(word in message_lower for word in ["vendor topic", "discussion", "negotiation", "meeting ask", "ask"]):
        content = _content_for(company_name, "highlights_vendor_topics.json")
        try:
            topics = json.loads(content) if isinstance(content, str) else content
            if isinstance(topics, dict):
                lines = []
                for topic in list(topics.values())[:3]:
                    summary = topic.get("summary") or topic.get("context")
                    ask = topic.get("discussion_point")
                    if summary and ask:
                        lines.append(f"{summary} Meeting ask: {ask}")
                if lines:
                    return f"{' '.join(lines)}\nSource: Vendor Discussion Topics"
        except Exception:
            pass
        return fallback_chatbot_answer(company_name, message, str(content))

    if any(word in message_lower for word in ["briefing", "risk", "opportunity", "recommended action"]):
        content = _content_for(company_name, "briefing.json")
        if isinstance(content, dict):
            summary = content.get("financial_health") or content.get("account_summary", {}).get("company_overview")
            risks = content.get("opportunities_risks", {}).get("risks", [])
            if summary:
                answer = summary
                if risks:
                    answer += " Key risks: " + " ".join(risks[:2])
                return f"{answer}\nSource: Briefing Docs"
        return fallback_chatbot_answer(company_name, message, str(content))

    if any(word in message_lower for word in ["earning", "revenue", "eps", "highlight", "takeaway"]):
        content = _content_for(company_name, "earnings.json")
        bullets = _bullets_from_markdown(content)
        answer = _first_paragraph(content) or "Earnings data is available for this vendor."
        if bullets:
            answer += " Key takeaways: " + " ".join(bullets[:3])
        return f"{answer}\nSource: Earnings"

    return None

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SummaryRequest(BaseModel):
    company_name: str

class ChatbotRequest(BaseModel):
    company_name: str  # Company name to load specific vector DB
    message: str
    history: list = []

class EarningsRequest(BaseModel):
    company_name: str
    force_live: bool = False

class HighlightsRequest(BaseModel):
    company_name: str
    tab: str  # vendor_topics, pricing_insights, products_features, ai_cloud_productivity, meta_synergies, or meta_spend_metrics

class QBRRequest(BaseModel):
    company_name: str

class BriefingRequest(BaseModel):
    company_name: str

@app.post("/earnings")
def get_earnings(request: EarningsRequest):
    """
    Fetch earnings data using the earning_summary_agent
    Returns structured earnings metrics and summary for display
    """
    try:
        earnings_data = load_mock_json(request.company_name, "earnings.json")
        if earnings_data and not request.force_live:
            return {
                "success": True,
                "company": request.company_name,
                "earnings": earnings_data,
                "fallback": True
            }

        if not has_preloaded_vendor_data(request.company_name) and not request.force_live:
            return {
                "success": True,
                "company": request.company_name,
                "earnings": {
                    "content": f"## Earnings\n\n{no_preloaded_data_message(request.company_name)}",
                    "sources": []
                },
                "missing_data": True
            }

        if Config.OFFLINE_MODE:
            mock_path = os.path.join("mock_data", request.company_name.lower(), "earnings.json")
            if os.path.exists(mock_path):
                with open(mock_path, "r") as f:
                    earnings_data = json.load(f)
                return {
                    "success": True,
                    "company": request.company_name,
                    "earnings": earnings_data
                }
            else:
                return {
                    "success": False,
                    "company": request.company_name,
                    "error": "Mock data not found for this company in offline mode."
                }

        from agents.earning_summary_agent import get_earnings_data

        earnings_data = get_earnings_data(request.company_name)
        return {
            "success": True,
            "company": request.company_name,
            "earnings": earnings_data
        }
        
    except Exception as e:
        import traceback
        print("ERROR in /earnings endpoint:")
        traceback.print_exc()
        earnings_data = load_mock_json(request.company_name, "earnings.json")
        if earnings_data:
            return {
                "success": True,
                "company": request.company_name,
                "earnings": earnings_data,
                "fallback": True
            }
        raise HTTPException(status_code=500, detail=f"Earnings fetch error: {str(e)}")


@app.post("/chatbot")
def chatbot(request: ChatbotRequest):
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from utils.llm_client import LLMClient

        direct_answer = answer_from_dashboard_data(request.company_name, request.message)
        if direct_answer:
            return {
                "response": direct_answer,
                "history": request.history + [
                    {"role": "user", "content": request.message},
                    {"role": "assistant", "content": direct_answer}
                ]
            }

        context = build_chatbot_context(request.company_name, request.message)
        if not context:
            answer = fallback_chatbot_answer(request.company_name, request.message, context)
        else:
            prompt = f"""
Company: {request.company_name}

Dashboard context:
{context[:5000]}

User question:
{request.message}

Answer using only the dashboard context above. Keep it concise, 2-4 sentences.
End with a source line in this exact format:
Source: Local Dashboard Data
""".strip()

            try:
                llm = LLMClient().get_llm()
                response = llm.invoke([
                    SystemMessage(content="You are a concise vendor intelligence assistant for a dashboard."),
                    HumanMessage(content=prompt),
                ])
                answer = response.content if hasattr(response, "content") else str(response)
            except Exception as llm_error:
                print(f"Ollama chatbot fallback used: {llm_error}")
                answer = fallback_chatbot_answer(request.company_name, request.message, context)

        # Update history
        updated_history = request.history + [
            {"role": "user", "content": request.message},
            {"role": "assistant", "content": answer}
        ]

        return {
            "response": answer,
            "history": updated_history
        }

    except Exception as e:
        print(f"Chatbot Error: {e}") # Debug print
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/summary")
def generate_summary(request: SummaryRequest):
    try:
        if Config.OFFLINE_MODE:
            mock_path = os.path.join("mock_data", request.company_name.lower(), "earnings.json")
            if os.path.exists(mock_path):
                with open(mock_path, "r") as f:
                    earnings_data = json.load(f)
                return {"summary": earnings_data.get("summary", "No summary found in mock data.")}
            else:
                return {"summary": "Mock summary not found in offline mode."}

        from agents.summary_agent import agent as summary_agent

        # Invoke the agent
        result = summary_agent.invoke({"company_name": request.company_name})
        
        # Extract content from the result structure
        # The agent returns {"messages": [{"role": "assistant", "content": "..."}]}
        messages = result.get("messages", [])
        if not messages:
            raise ValueError("No summary generated.")
            
        final_message = messages[-1]
        content = final_message.get("content") if isinstance(final_message, dict) else final_message.content
        
        return {"summary": content}
    except Exception as e:
        earnings_data = load_mock_json(request.company_name, "earnings.json")
        if earnings_data:
            return {"summary": earnings_data.get("summary", "No summary found in mock data."), "fallback": True}
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stock-data", response_model=StockDataResponse)
def get_stock_data(request: StockRequest):
    return fetch_stock_data(request.company_name)

@app.post("/highlights")
def get_highlights(request: HighlightsRequest):
    """
    Fetch highlights data for a specific tab
    Returns pricing insights, products/features, or AI/cloud/productivity data
    """
    try:
        mock_file = f"highlights_{request.tab}.json"
        fallback_data = load_mock_json(request.company_name, mock_file)
        if fallback_data:
            return {
                "success": True,
                "company": request.company_name,
                "tab": request.tab,
                "data": fallback_data,
                "fallback": True
            }

        if not has_preloaded_vendor_data(request.company_name):
            return {
                "success": True,
                "company": request.company_name,
                "tab": request.tab,
                "data": no_preloaded_highlight(request.company_name, request.tab),
                "missing_data": True
            }

        if Config.OFFLINE_MODE:
            mock_path = os.path.join("mock_data", request.company_name.lower(), mock_file)
            if os.path.exists(mock_path):
                with open(mock_path, "r") as f:
                    data = json.load(f)
                return {
                    "success": True,
                    "company": request.company_name,
                    "tab": request.tab,
                    "data": data
                }
            else:
                return {
                    "success": True,
                    "company": request.company_name,
                    "tab": request.tab,
                    "data": {"content": f"Mock data for {request.tab} not available in offline mode.", "sources": []}
                }

        import asyncio
        from tools.ai_cloud_productivity_tool import get_ai_cloud_productivity
        from tools.pricing_insights_tool import get_pricing_insights
        from tools.products_features_tool import get_products_features
        from tools.vendor_discussion_topics_tool import get_vendor_discussion_topics
        from tools.leadership_tool import get_leadership

        tab_functions = {
            "leadership": get_leadership,
            "pricing_insights": get_pricing_insights,
            "products_features": get_products_features,
            "vendor_topics": get_vendor_discussion_topics,
            "ai_cloud_productivity": get_ai_cloud_productivity
        }

        func = tab_functions.get(request.tab)
        if not func:
            return {
                "success": False,
                "company": request.company_name,
                "tab": request.tab,
                "error": f"Invalid highlights tab: {request.tab}"
            }

        # Execute tool function and parse its JSON response string
        result_str = func.invoke(request.company_name)
        result_data = json.loads(result_str)

        return {
            "success": True,
            "company": request.company_name,
            "tab": request.tab,
            "data": result_data
        }
        
    except Exception as e:
        import traceback
        print("ERROR in /highlights endpoint:")
        traceback.print_exc()
        mock_file = f"highlights_{request.tab}.json"
        fallback_data = load_mock_json(request.company_name, mock_file)
        if fallback_data:
            return {
                "success": True,
                "company": request.company_name,
                "tab": request.tab,
                "data": fallback_data,
                "fallback": True
            }
        raise HTTPException(status_code=500, detail=f"Highlights fetch error: {str(e)}")

@app.post("/qbr")
def get_qbr(request: QBRRequest):
    """
    Generate QBR (Quarterly Business Review) report for a company
    Returns comprehensive business performance analysis
    """
    try:
        if not has_preloaded_vendor_data(request.company_name):
            return {
                "success": True,
                "company": request.company_name,
                "qbr": {
                    "content": f"## QBR\n\n{no_preloaded_data_message(request.company_name)}",
                    "report_type": "qbr"
                },
                "missing_data": True
            }

        if Config.OFFLINE_MODE:
            mock_path = os.path.join("mock_data", request.company_name.lower(), "qbr.md")
            if os.path.exists(mock_path):
                with open(mock_path, "r") as f:
                    content = f.read()
                return {
                    "success": True,
                    "company": request.company_name,
                    "qbr": {"content": content, "report_type": "qbr"}
                }
            else:
                return {
                    "success": False,
                    "company": request.company_name,
                    "error": "Mock QBR not found in offline mode."
                }

        import time
        from agents.qbr_agent import get_qbr_data
        
        # Artificial delay removed
        
        qbr_data = get_qbr_data(request.company_name)
        
        return {
            "success": True,
            "company": request.company_name,
            "qbr": qbr_data
        }
        
    except Exception as e:
        import traceback
        print("ERROR in /qbr endpoint:")
        traceback.print_exc()
        content = load_mock_text(request.company_name, "qbr.md")
        if content:
            return {
                "success": True,
                "company": request.company_name,
                "qbr": {"content": content, "report_type": "qbr"},
                "fallback": True
            }
        raise HTTPException(status_code=500, detail=f"QBR fetch error: {str(e)}")



@app.post("/briefing")
def get_briefing(request: BriefingRequest):
    """
    Generate Briefing Document for a company
    Returns comprehensive briefing doc with context, risks, and asks
    """
    try:
        content_json = load_mock_json(request.company_name, "briefing.json")
        if content_json:
            return {
                "success": True,
                "company": request.company_name,
                "briefing": {
                    "content": json.dumps(content_json),
                    "doc_type": "briefing"
                },
                "fallback": True
            }

        if not has_preloaded_vendor_data(request.company_name):
            return {
                "success": True,
                "company": request.company_name,
                "briefing": {
                    "content": json.dumps({
                        "financial_health": no_preloaded_data_message(request.company_name),
                        "account_summary": {
                            "company_overview": no_preloaded_data_message(request.company_name),
                            "key_highlights": []
                        },
                        "business_performance": {
                            "strengths": [],
                            "challenges": []
                        },
                        "opportunities_risks": {
                            "opportunities": [],
                            "risks": []
                        },
                        "recommended_actions": [
                            "Add vendor-specific source files or generate live data before using this briefing."
                        ]
                    }),
                    "doc_type": "briefing"
                },
                "missing_data": True
            }

        if Config.OFFLINE_MODE:
            mock_path = os.path.join("mock_data", request.company_name.lower(), "briefing.json")
            if os.path.exists(mock_path):
                with open(mock_path, "r", encoding="utf-8") as f:
                    content_json = json.load(f)
                return {
                    "success": True,
                    "company": request.company_name,
                    "briefing": {
                        "content": json.dumps(content_json),
                        "doc_type": "briefing"
                    }
                }
            else:
                return {
                    "success": False,
                    "company": request.company_name,
                    "error": "Mock Briefing not found in offline mode."
                }

        import time
        
        # Artificial delay removed

        from agents.briefing_agent import get_briefing_data
        
        # Get Briefing Doc
        briefing_data = get_briefing_data(request.company_name)
        
        return {
            "success": True,
            "company": request.company_name,
            "briefing": briefing_data
        }
        
    except Exception as e:
        import traceback
        print("ERROR in /briefing endpoint:")
        traceback.print_exc()
        content_json = load_mock_json(request.company_name, "briefing.json")
        if content_json:
            return {
                "success": True,
                "company": request.company_name,
                "briefing": {
                    "content": json.dumps(content_json),
                    "doc_type": "briefing"
                },
                "fallback": True
            }
        raise HTTPException(status_code=500, detail=f"Briefing fetch error: {str(e)}")


@app.post("/company-metrics", response_model=CompanyMetricsResponse)
def get_company_metrics(request: CompanyMetricsRequest):
    return fetch_company_metrics(request.company_name)


class UpdatePromptRequest(BaseModel):
    filename: str
    content: str


ALLOWED_PROMPTS = {
    "price_insight_prompt.txt": "Price Insight Prompt",
    "vendor_topics_prompt.txt": "Vendor Topics Prompt",
    "product_features_prompt.txt": "Products & Features Prompt",
    "ai_cloud_productivity_prompt.txt": "AI & Cloud Productivity Prompt"
}


@app.get("/api/prompts")
async def get_prompts():
    """
    Get all configurable system prompts
    """
    try:
        prompts = {}
        for filename in ALLOWED_PROMPTS.keys():
            path = Config.PROMPTS_DIR / filename
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    prompts[filename] = f.read()
            else:
                prompts[filename] = ""
        return {
            "success": True,
            "prompts": prompts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load prompts: {str(e)}")


@app.post("/api/prompts")
async def update_prompt(request: UpdatePromptRequest):
    """
    Update a specific system prompt
    """
    if request.filename not in ALLOWED_PROMPTS:
        raise HTTPException(status_code=400, detail="Invalid prompt filename")
    
    try:
        path = Config.PROMPTS_DIR / request.filename
        # Ensure the prompts directory exists
        os.makedirs(Config.PROMPTS_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(request.content)
        return {
            "success": True,
            "message": f"Prompt '{request.filename}' updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update prompt: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001)
