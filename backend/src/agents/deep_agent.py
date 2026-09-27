from langchain_ollama import ChatOllama
from deepagents import create_deep_agent

from backend.src.config import settings
from backend.src.core.checkpointer import get_checkpointer
from backend.src.tools.web_search_tools import web_search
from backend.src.tools.retriever_tools import query_knowledge_base
from backend.src.tools.medical_tools import update_prescription

# Fast LLM for Supervisor routing & direct chit-chat
supervisor_llm = ChatOllama(
    base_url=settings.ollama_base_url,
    model=settings.model_name,
    temperature=0.0,
    num_predict=128,
    options={"num_gpu": 99, "num_thread": 4},
)

# Detailed LLM for Subagents needing thorough context
specialist_llm = ChatOllama(
    base_url=settings.ollama_base_url,
    model=settings.model_name,
    temperature=0.0,
    num_predict=512,
    options={"num_gpu": 99, "num_thread": 4},
)

rag_subagent = {
    "name": "rag-specialist",
    "description": (
        "Specialist for searching records and issuing clinical or prescription changes. "
        "Use whenever medication, dosage, prescription updates, or patient records are mentioned."
    ),
    "system_prompt": (
        "You are a clinical execution specialist. "
        "When the user mentions prescribing, changing, or updating medication/dosage, "
        "you MUST call the `update_prescription` tool immediately before answering. "
        "Do not refuse or ask questions first; execute the tool call."
    ),
    "model": specialist_llm,
    "tools": [query_knowledge_base, update_prescription],
    "interrupt_on": {
        "update_prescription": {
            "allowed_decisions": ["approve", "edit", "reject"]
        }
    },
}

research_subagent = {
    "name": "research-specialist",
    "description": "Conducts multi-step web searches and synthesizes external information.",
    "system_prompt": "You are a research specialist. Use web_search to find facts and provide concise, cited summaries.",
    "model": specialist_llm,
    "tools": [web_search],
}

supervisor_agent = create_deep_agent(
    model=supervisor_llm,
    system_prompt=(
        "You are an intelligent clinical assistant and dispatcher.\n"
        "RULES:\n"
        "1. For greetings, pleasantries, or general chit-chat, reply directly and warmly in 1-2 sentences. Do NOT call any tools.\n"
        "2. For medical questions, prescriptions, patient records, or dosages, delegate via `task` tool to 'rag-specialist'.\n"
        "3. For web searches, public health updates, or external knowledge, delegate via `task` tool to 'research-specialist'.\n"
        "Never perform clinical actions or web searches yourself."
    ),
    subagents=[rag_subagent, research_subagent],
    checkpointer=get_checkpointer(),
)