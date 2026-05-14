import os
from fastapi import FastAPI, Request, HTTPException
import uvicorn
from dotenv import load_dotenv
load_dotenv()
from agent_logic import ContractAgent, STATE_FILE

app = FastAPI(title="Anti Gravity Orchestrator Webhook", version="1.0")

# Initialize the stateful Agent
agent = ContractAgent()

@app.on_event("startup")
async def startup_event():
    """
    Restart from the first step of the workflow when the program starts
    so it is easier to test and do changes.
    """
    print("[System] Clearing state to restart from the first step...")
    agent.state = {}
    if os.path.exists(STATE_FILE):
        try:
            os.remove(STATE_FILE)
        except Exception as e:
            print(f"[System] Could not remove state file: {e}")
    agent.save_state()
    
    print("[System] Triggering the first step of the workflow...")
    # Fire the initial trigger to send the first email (Planning phase)
    await agent.execute_agent_loop({"contract_id": "C-1064"})

@app.post("/webhook")
async def receive_webhook(request: Request):
    """
    Receives incoming Gmail push notifications via Google Cloud Pub/Sub.
    Expects a payload with info about the 180-day alert email.
    """
    try:
        payload = await request.json()
        print(f"[Webhook] Received Payload: {payload}")
        
        # Pass the observation to the Agent
        # A true system would decode message.data, parse email headers, and extract Contract_ID.
        await agent.execute_agent_loop(payload)
        
        return {"status": "success", "message": "Agent processing initiated."}
    except Exception as e:
        print(f"[Webhook] Error processing payload: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid payload")

@app.get("/action/{contract_id}/{stage_action}")
async def handle_agent_action(contract_id: str, stage_action: str):
    """
    Endpoint invoked when a user clicks an action button in the relay email.
    """
    print(f"[Action] Triggered transition for {contract_id} to {stage_action}")
    
    # Tool: Update Stage
    agent.call_tool_update_stage(contract_id, stage_action)
    
    # We trigger the agent loop again to see if there is an immediate next action to push
    dummy_payload = {"contract_id": contract_id}
    await agent.execute_agent_loop(dummy_payload)
    
    return {"status": "success", "message": f"Contract {contract_id} transitioned to '{stage_action}' successfully. Check dashboard or next email."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

