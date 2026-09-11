import chromadb
from langchain_core.tools import tool
from langchain_ollama import OllamaEmbeddings
from src.config import settings

# Connect to the ChromaDB Docker container
chroma_client = chromadb.HttpClient(
    host=settings.chroma_host,
    port=settings.chroma_port
)

# Embedding model through Ollama
embeddings = OllamaEmbeddings(
    base_url=settings.ollama_base_url,
    model=settings.embedding_model
)

@tool
def query_knowledge_base(query: str) -> str:
    """Search internal clinical and operational records in ChromaDB."""
    try:
        collection = chroma_client.get_or_create_collection("knowledge_base")
        query_vector = embeddings.embed_query(query)
        
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=2
        )
        
        docs = results.get("documents", [[]])[0]
        if not docs:
            return "No relevant records found in knowledge base."
        return "\n---\n".join(docs)
    except Exception as e:
        return f"Error retrieving from knowledge base: {str(e)}"