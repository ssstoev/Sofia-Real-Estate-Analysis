'''Chat Endpoint'''
from agent.main import agent
from pydantic import BaseModel
from fastapi import APIRouter

# define an api router
router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: str

conversation_store = {}

@router.post("/chat")
async def chat(request: ChatRequest):
    history = conversation_store.get(request.session_id, [])
    
    response, listings = await agent(request.message, history)
    
    history.append({"role": "user", "content": request.message})
    history.append({"role": "assistant", "content": response})
    conversation_store[request.session_id] = history[-10:]
    
    return {"response": response, "listings": listings}