import hashlib
from fastapi import APIRouter, HTTPException, Request
from app.models.chat import ChatRequest, ChatResponse
import logging
from app.services.rag.rag_service import query_rag_chain

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(request:Request,
    payload: ChatRequest,
):
    """
    Customer-facing chat endpoint.
    Receives a query and returns an AI-generated response based on context.
    """
    user_agent = request.headers.get("user-agent", "default")
    thread_id = hashlib.md5(user_agent.encode()).hexdigest()
    try:

        response_text = await query_rag_chain(question=payload.query, thread_id=thread_id)
        return ChatResponse(response=response_text)
    except Exception as e:
        logging.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get AI response: {e}")
