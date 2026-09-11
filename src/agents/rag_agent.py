from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.types import interrupt

from src.config import settings
from src.tools.retriever_tools import query_knowledge_base
from src.hitl.policies import requires_human_review
from src.hitl.actions import build_review_payload

llm = ChatOllama(
    base_url=settings.ollama_base_url,
    model=settings.model_name,
    temperature=0.1
)

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