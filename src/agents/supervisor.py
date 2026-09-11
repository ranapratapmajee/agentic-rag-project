from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from src.config import settings
from src.agents.chat_agent import chat_specialist
from src.agents.rag_agent import rag_specialist

llm = ChatOllama(
    base_url=settings.ollama_base_url,
    model=settings.model_name,
    temperature=0.0
)

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