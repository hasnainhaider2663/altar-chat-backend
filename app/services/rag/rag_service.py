from typing import Annotated, List, Literal, TypedDict, Dict, Any
from langchain_core.documents import Document
from app.database.connection import get_pgvector_store
from langchain_core.prompts import PromptTemplate
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import os
from langgraph.graph import StateGraph, START, END
import logging
from langgraph.checkpoint.memory import MemorySaver


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")


template = """You are an Assistant chatbot for the Altar.io Website. Altar.io builds products for startups.Use the following pieces of context to answer the question at the end.

If you don't know the answer, just say that you don't know, don't try to make up an answer.
Use three sentences maximum and keep the answer as concise as possible.

Be mindful of the following guidelines:
    1.  **Only use provided context:** Kindly base your answers exclusively on the information given in the "Context" section.
    2.  **State limitations politely:** If you don't have enough information to answer a question based on the provided "Context," please politely state that you cannot assist with that specific query at this time. Kindly avoid guessing or fabricating details.
    3.  **Be concise and professional:** Deliver information directly and clearly, maintaining a helpful and respectful tone.
    4.  **Prioritize Altar.io information:** Always focus your responses on Altar.io's offerings and capabilities.

{context}

Helpful Answer:"""

prompt = PromptTemplate.from_template(template)


class Search(TypedDict):
    """Search query."""

    query: Annotated[str, ..., "Search query to run."]
    section: Annotated[
        Literal["beginning", "middle", "end"],
        ...,
        "Section to query.",
    ]


class State(TypedDict):
    """State for the RAG application."""

    question: str
    context: List[Document]
    answer: str
    query: Search


def analyze_query(state: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the query and structure it."""
    try:
        structured_llm = llm.with_structured_output(Search)
        query = structured_llm.invoke(state["question"])
        return {"query": query}
    except Exception as e:
        logging.error(f"Error in analyze_query: {e}")
        return {"query": {"query": state["question"], "section": "middle"}}


def retrieve(state: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve relevant documents."""
    try:
        query = state["query"]
        store = get_pgvector_store()
        retrieved_docs = store.similarity_search(
            query["query"],
            k=2,  # Limit results
        )
        return {"context": retrieved_docs}
    except Exception as e:
        logging.error(f"Error in retrieve: {e}")
        return {"context": []}


def generate(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate the final answer."""
    try:
        # Combine document content
        docs_content = "\n\n".join(doc.page_content for doc in state["context"])

        # Format prompt
        formatted_prompt = template.format(
            context=docs_content, question=state["question"]
        )

        # Get response from LLM
        response = llm.invoke(formatted_prompt)
        return {
            "answer": (
                response.content if hasattr(response, "content") else str(response)
            )
        }
    except Exception as e:
        logging.error(f"Error in generate: {e}")
        return {
            "answer": "I apologize, but I encountered an error processing your request. Thanks for asking!"
        }


async def create_rag_chain():
    """Create and return the RAG chain."""
    try:
        # Initialize graph builder with proper typing
        graph = StateGraph(State)

        # Add nodes
        graph.add_node("analyze_query", analyze_query)
        graph.add_node("retrieve", retrieve)
        graph.add_node("generate", generate)

        # Add edges
        graph.add_edge(START, "analyze_query")
        graph.add_edge("analyze_query", "retrieve")
        graph.add_edge("retrieve", "generate")
        graph.add_edge("generate", END)
        memory = MemorySaver()

        return graph.compile(checkpointer=memory)
    except Exception as e:
        logging.error(f"Error creating RAG chain: {e}")
        raise


async def query_rag_chain(question: str, thread_id: str) -> str:
    """Query the RAG chain with a question."""
    try:
        chain = await create_rag_chain()

        # Initialize state
        initial_state: State = {
            "question": question,
            "context": [],
            "answer": "",
            "query": {"query": "", "section": "middle"},
        }
        config = {"configurable": {"thread_id": thread_id}}

        # Run chain
        result = await chain.ainvoke(initial_state, config=config)
        return result["answer"]
    except Exception as e:
        logging.error(f"Error querying RAG chain: {e}")
        return "I apologize, but I encountered an error processing your request."
