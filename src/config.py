import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # LLM (Ollama)
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model_name: str = os.getenv("MODEL_NAME", "llama3.2:1b")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

    # ChromaDB (Docker Service)
    chroma_host: str = os.getenv("CHROMA_HOST", "localhost")
    chroma_port: int = int(os.getenv("CHROMA_PORT", "8000"))

    # HITL and Guardrails
    retrieval_confidence_threshold: float = float(os.getenv("RETRIEVAL_CONFIDENCE_THRESHOLD", "0.70"))
    hitl_enabled: bool = os.getenv("HITL_ENABLED", "true").lower() == "true"

settings = Settings()