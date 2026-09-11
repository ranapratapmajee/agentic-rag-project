from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from src.config import settings

llm = ChatOllama(
    base_url=settings.ollama_base_url,
    model=settings.model_name,
    temperature=0.7
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