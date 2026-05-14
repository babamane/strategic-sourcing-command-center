from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Add project root to path for imports
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from agents.summary_agent import agent as summary_agent
from main import fetch_stock_data, fetch_company_metrics, StockDataResponse, CompanyMetricsResponse, StockRequest, CompanyMetricsRequest

app = FastAPI(title="Earning Docs API", version="1.0.0")

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

class HighlightsRequest(BaseModel):
    company_name: str
    tab: str  # vendor_topics, pricing_insights, products_features, ai_cloud_productivity, meta_synergies, or meta_spend_metrics

class QBRRequest(BaseModel):
    company_name: str

class BriefingRequest(BaseModel):
    company_name: str

@app.post("/earnings")
async def get_earnings(request: EarningsRequest):
    """
    Fetch earnings data using the earning_summary_agent
    Returns structured earnings metrics and summary for display
    """
    try:
        from agents.earning_summary_agent import get_earnings_data
        
        # Delegate to the agent
        earnings_data = get_earnings_data(request.company_name)
        
        # Return formatted response
        return {
            "success": True,
            "company": request.company_name,
            "earnings": earnings_data
        }
        
    except Exception as e:
        import traceback
        print("ERROR in /earnings endpoint:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Earnings fetch error: {str(e)}")


@app.post("/chatbot")
async def chatbot(request: ChatbotRequest):
    try:
        from agents.chatbot_agent import chatbot_agent
        from langchain_core.messages import HumanMessage, AIMessage

        # Prepare messages list with history
        messages = []
        print(f"DEBUG: Received history: {request.history}") # Debug log
        
        for msg in request.history:
            # Ensure keys exist
            role = msg.get('role', 'user') # Default to user if missing
            content = msg.get('content', '')
            
            # Map 'bot' to 'assistant' if needed (frontend uses 'bot')
            if role == 'bot':
                role = 'assistant'
                
            messages.append({"role": role, "content": content})
            
        # Add current user message with context
        contextualized_input = f"For company '{request.company_name}': {request.message}"
        messages.append({"role": "user", "content": contextualized_input})

        # Run the agent
        # Using the same pattern as earning_agent
        response = chatbot_agent.invoke({
            "messages": messages
        })

        # Extract answer
        # The response format depends on the agent type. 
        # If it's the same as earning_agent, the last message is the answer.
        final_message = response["messages"][-1]
        answer = final_message.content if hasattr(final_message, 'content') else str(final_message)

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
async def generate_summary(request: SummaryRequest):
    try:
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
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/stock-data", response_model=StockDataResponse)
def get_stock_data(request: StockRequest):
    return fetch_stock_data(request.company_name)

@app.post("/highlights")
async def get_highlights(request: HighlightsRequest):
    """
    Fetch highlights data for a specific tab
    Returns pricing insights, products/features, or AI/cloud/productivity data
    """
    try:
        import asyncio
        import random
        
        # Add realistic delay (5-8 seconds) to simulate processing
        delay = random.uniform(5, 8)
        await asyncio.sleep(delay)
        
        from agents.highlights_agent import (
            get_pricing_insights_data,
            get_products_features_data,
            get_ai_cloud_productivity_data,
            get_vendor_discussion_topics_data,
            get_meta_synergies_data,
            get_meta_spend_metrics_data
        )
        
        # Route to appropriate function based on tab
        if request.tab == "vendor_topics":
            data = get_vendor_discussion_topics_data(request.company_name)
        elif request.tab == "pricing_insights":
            data = get_pricing_insights_data(request.company_name)
        elif request.tab == "products_features":
            data = get_products_features_data(request.company_name)
        elif request.tab == "ai_cloud_productivity":
            data = get_ai_cloud_productivity_data(request.company_name)
        elif request.tab == "meta_synergies":
            data = get_meta_synergies_data(request.company_name)
        elif request.tab == "meta_spend_metrics":
            data = get_meta_spend_metrics_data(request.company_name)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid tab: {request.tab}")
        
        return {
            "success": True,
            "company": request.company_name,
            "tab": request.tab,
            "data": data
        }
        
    except Exception as e:
        import traceback
        print("ERROR in /highlights endpoint:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Highlights fetch error: {str(e)}")

@app.post("/qbr")
async def get_qbr(request: QBRRequest):
    """
    Generate QBR (Quarterly Business Review) report for a company
    Returns comprehensive business performance analysis
    """
    try:
        import asyncio
        
        # Add 8-second delay to simulate report generation
        await asyncio.sleep(8)
        
        from agents.qbr_agent import get_qbr_data
        
        # Get QBR report
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
        raise HTTPException(status_code=500, detail=f"QBR fetch error: {str(e)}")



@app.post("/briefing")
async def get_briefing(request: BriefingRequest):
    """
    Generate Briefing Document for a company
    Returns comprehensive briefing doc with context, risks, and asks
    """
    try:
        import asyncio
        
        # Add 8-second delay to simulate document generation
        await asyncio.sleep(8)

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
        raise HTTPException(status_code=500, detail=f"Briefing fetch error: {str(e)}")


@app.post("/company-metrics", response_model=CompanyMetricsResponse)
def get_company_metrics(request: CompanyMetricsRequest):
    return fetch_company_metrics(request.company_name)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
