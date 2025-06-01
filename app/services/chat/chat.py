import logging
import os

from fastapi import HTTPException
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from ..rag.rag_service import query_rag_chain

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")


async def generate_response(
    query: str,
):

    try:
        response = await query_rag_chain( query)
        return response
    except Exception as e:
        logging.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get AI response: {e}")
