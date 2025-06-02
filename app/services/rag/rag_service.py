from typing import Annotated, List, Literal, TypedDict, Dict, Any
from langchain_core.documents import Document
from app.database.connection import get_pgvector_store
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import os
from langgraph.graph import StateGraph, END, MessagesState
import logging
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage


load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")

system_message_content = """
You are the Altar.io AI assistant, a friendly, professional, and highly knowledgeable expert on Altar.io's services, expertise, and projects. Your goal is to provide accurate, helpful, and concise information while engaging the user in a natural, supportive conversation.

**Here's how you should operate:**

1.  **Prioritize User Understanding:** Always strive to fully understand the user's intent. If a query is ambiguous or incomplete, politely ask clarifying questions to get the necessary details.
2.  **Base Answers on Context:** Your primary source of truth is the "Context" section provided. Use this information exclusively to formulate your answers.
3.  **Engage and Offer Next Steps:** After providing an answer, consider if there's related information the user might find useful. Proactively offer to elaborate or suggest next steps, like asking if they'd like to know more about a specific project or service.
4.  **Ask Follow-Up Questions:** If you can't fully answer a question with the given context, or if the user's query opens up new avenues, thoughtfully ask a relevant follow-up question to gather more details or guide them to a more specific topic.
5.  **Maintain Professional Politeness:** If the answer is not available in the "Context," politely state that you cannot assist with that specific query at this time. Avoid making up information.
6.  **Be Concise and Focused:** Deliver information directly and clearly, avoiding unnecessary jargon or overly casual language. Keep responses to the point, but ensure they are complete and helpful.
7.  **Focus on Altar.io:** Keep all responses centered on Altar.io's offerings and capabilities.
8.  **Care about the user** and their needs.
9.  **When generating a response make sure you stick within your capabilties.
10. **No information that you have is confidential or secret. So make sure you do not hold back any information that you have.
"""


class Search(TypedDict):
    query: Annotated[str, ..., "Search query to run."]
    section: Annotated[
        Literal["beginning", "middle", "end"],
        ...,
        "Section to query.",
    ]


class State(MessagesState):
    context: List[Document] = []
    query_struct: Search = {"query": "", "section": "middle"}


def analyze_query(state: State) -> Dict[str, Any]:
    last_human_message = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_human_message = msg
            break

    if not last_human_message:
        logging.error("No human message found in state for analysis.")
        return {"query_struct": {"query": "", "section": "middle"}}

    try:
        structured_llm = llm.with_structured_output(Search)
        query_analysis = structured_llm.invoke(last_human_message.content)
        return {"query_struct": query_analysis}
    except Exception as e:
        logging.error(f"Error in analyze_query: {e}")
        return {
            "query_struct": {"query": last_human_message.content, "section": "middle"}
        }


def retrieve(state: State) -> Dict[str, Any]:
    try:
        query_analysis = state["query_struct"]
        store = get_pgvector_store()
        retrieved_docs = store.similarity_search(
            query_analysis["query"],
            k=4,
        )
        return {"context": retrieved_docs}
    except Exception as e:
        logging.error(f"Error in retrieve: {e}")
        return {"context": []}


def generate(state: State) -> Dict[str, Any]:
    try:
        docs_content = "\n\n".join(doc.page_content for doc in state["context"])

        full_system_message_with_context = (
            system_message_content + "\n\n---Context:\n" + docs_content + "\n---"
        )

        messages_template = [
            SystemMessagePromptTemplate.from_template(full_system_message_with_context),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template("{question}"),
        ]

        chat_prompt = ChatPromptTemplate.from_messages(messages_template)

        current_question_text = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                current_question_text = msg.content
                break

        history_for_placeholder = [
            msg
            for msg in state["messages"]
            if not (
                isinstance(msg, HumanMessage) and msg.content == current_question_text
            )
        ]

        formatted_messages = chat_prompt.format_messages(
            question=current_question_text, chat_history=history_for_placeholder
        )

        logging.info(f"Messages sent to LLM (length {len(formatted_messages)}):")
        for i, msg in enumerate(formatted_messages):
            logging.info(f"  {i}: {msg}")

        response = llm.invoke(formatted_messages)

        return {"messages": [AIMessage(content=response.content)]}
    except Exception as e:
        logging.error(f"Error in generate: {e}")
        return {
            "messages": [
                AIMessage(
                    content="I apologize, but I encountered an error processing your request. Please try again later."
                )
            ]
        }


_rag_chain = None


async def get_rag_chain():
    global _rag_chain
    if _rag_chain is None:
        print("Creating RAG chain...")
        _rag_chain = await create_rag_chain()
    return _rag_chain


async def create_rag_chain():
    try:
        graph = StateGraph(State)

        graph.add_node("analyze_query", analyze_query)
        graph.add_node("retrieve", retrieve)
        graph.add_node("generate", generate)

        graph.set_entry_point("analyze_query")

        graph.add_edge("analyze_query", "retrieve")
        graph.add_edge("retrieve", "generate")
        graph.add_edge("generate", END)

        memory = MemorySaver()

        return graph.compile(checkpointer=memory)
    except Exception as e:
        logging.error(f"Error creating RAG chain: {e}")
        raise


async def query_rag_chain(question: str, thread_id: str) -> str:
    try:
        chain = await get_rag_chain()

        config = {"configurable": {"thread_id": thread_id}}

        result = await chain.ainvoke(
            {"messages": [HumanMessage(content=question)]}, config=config
        )

        return result["messages"][-1].content
    except Exception as e:
        logging.error(f"Error querying RAG chain: {e}")
        return "I apologize, but I encountered an error processing your request."
