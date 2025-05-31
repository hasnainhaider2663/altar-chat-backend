from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from langchain_postgres import PGVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import settings
from app.models.document import LangchainPgVector
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL)


async def get_pgvector_store():
    """
    Initializes and returns the Langchain PGVector store.
    """
    try:
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001", api_key=settings.GOOGLE_API_KEY
        )
        store = PGVector(
            embeddings=embeddings,
            collection_name="altar_chatbot_collection",
            connection=DATABASE_URL,
            use_jsonb=True,
        )
        logging.info("PGVector store initialized successfully.")
        return store
    except Exception as e:
        logging.error(f"Failed to initialize PGVector store: {e}")
        raise
