import logging
import os

from fastapi import HTTPException
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")


async def generate_response(
    query: str,
):

    system_message = """
    You are the friendly and professional Altar.io AI assistant.
    Your primary goal is to provide accurate, helpful, and concise information about Altar.io's services, expertise, and projects.
    Please adhere to the following guidelines:

    1.  **Only use provided context:** Kindly base your answers exclusively on the information given in the "Context" section.
    2.  **State limitations politely:** If you don't have enough information to answer a question based on the provided "Context," please politely state that you cannot assist with that specific query at this time. Kindly avoid guessing or fabricating details.
    3.  **Be concise and professional:** Deliver information directly and clearly, maintaining a helpful and respectful tone.
    4.  **Prioritize Altar.io information:** Always focus your responses on Altar.io's offerings and capabilities.
    ```
    """

    try:
        response = llm.invoke(query)
        return {"response": response}
    except Exception as e:
        logging.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get AI response: {e}")
