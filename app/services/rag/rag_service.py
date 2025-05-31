from app.database.connection import get_pgvector_store


async def add_documents_to_store(documents):
    """
    Add documents to the RAG store.
    """
    pgvector_store = await get_pgvector_store()
    pgvector_store.add_documents(documents)