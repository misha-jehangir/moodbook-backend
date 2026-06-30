from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.auth.firebase_auth import get_current_user
from app.services.gemini_service import generate_chat_response_stream
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatMessage(BaseModel):
    role: str # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]

@router.post("")
async def chat_endpoint(request: ChatRequest, user: dict = Depends(get_current_user)):
    """
    Protected chat endpoint. Receives chat history, verifies the user's Firebase ID,
    and streams back the Gemini RAG wellness assistant response using Server-Sent Events (SSE).
    """
    user_id = user.get("uid")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user identification")
    
    # Convert Pydantic models to dictionaries
    history = [msg.model_dump() for msg in request.messages]
    
    # Define an async event generator for Server-Sent Events
    async def event_generator():
        # Iterate over the blocking generator from the Gemini service
        # and yield formatted SSE data chunks
        for chunk in generate_chat_response_stream(history, user_id):
            yield f"data: {chunk}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
