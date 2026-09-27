from backend.src.config import settings
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.types import interrupt

from backend.src.tools.retriever_tools import query_knowledge_base
from backend.src.hitl.policies import requires_human_review
from backend.src.hitl.actions import build_review_payload


llm = ChatOllama(
    base_url=settings.ollama_base_url,
    model=settings.model_name,
    temperature=0.0
)

# Sub-agent instance
chat_sub_agent = create_agent(
    model=llm,
    tools=[],
    system_prompt="You are a warm, empathetic assistant. Answer greetings and general casual queries clearly and concisely."
)

@tool
def chat_specialist(query: str) -> str:
    """Useful for greetings, casual chit-chat, empathy, and general conversational inquiries."""
    response = chat_sub_agent.invoke({"messages": [{"role": "user", "content": query}]})
    return response["messages"][-1].content

# Sub-agent instance with retriever tools
rag_sub_agent = create_agent(
    model=llm,
    tools=[query_knowledge_base],
    system_prompt="You are a medical & document search expert. Retrieve documents and summarize findings accurately."
)

@tool
def rag_specialist(query: str) -> str:
    """Useful for searching medical records, clinical notes, uploaded documents, and internal knowledge base."""
    # HITL Guard: Interrupt execution if sensitive/risky intent is detected
    if requires_human_review(query):
        payload = build_review_payload("High-risk medical query or document operation", query)
        decision = interrupt(payload)
        
        if not decision.get("approved", False):
            return f"Action blocked by reviewer: {decision.get('reason', 'Declined')}"

    response = rag_sub_agent.invoke({"messages": [{"role": "user", "content": query}]})
    return response["messages"][-1].content


# Supervisor agent has sub-agents as tools
supervisor_agent = create_agent(
    model=llm,
    tools=[chat_specialist, rag_specialist],
    system_prompt=(
        "You are the main supervisor agent orchestrating specialized sub-agents.\n"
        "- Delegate document searches, medical inquiries, and record queries to `rag_specialist`.\n"
        "- Delegate greetings, pleasantries, and general chit-chat to `chat_specialist`.\n"
        "Always relay the specialist's response back to the user."
    )
)