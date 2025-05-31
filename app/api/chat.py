from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest, ChatResponse
import logging
from app.services.chat.chat import generate_response

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_with_bot(
    request: ChatRequest,
):
    """
    Customer-facing chat endpoint.
    Receives a query and returns an AI-generated response based on context.
    """

    try:

        response_text = await generate_response(
            query=request.query,
        )
        return ChatResponse(response=f'{response_text} "{request.query}"')
    except Exception as e:
        logging.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get AI response: {e}")
