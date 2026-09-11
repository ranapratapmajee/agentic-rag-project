# Modular Agentic RAG with In-Memory Guardrails & Human-in-the-Loop (HITL)

A privacy-first, modular Agentic Retrieval-Augmented Generation (RAG) system built with **LangGraph**, **Microsoft Presidio**, **LangChain (`create_agent`)**, **Ollama**, and **Dockerized ChromaDB**.

The system implements a defense-in-depth architecture: incoming prompts undergo deterministic regex and NER-based PII/PHI de-identification before reaching any language model. Sub-agent tools execute within an isolated context, and state-suspension (**HITL**) halts execution dynamically whenever sensitive operations or low-confidence thresholds are encountered.

---

## Key Features

- **Bi-Directional In-Memory Guardrails**: Zero-leakage tokenization of sensitive PII/PHI (HIPAA Safe Harbor, SSN, MRN, Patient ID, phone, email, names) using Microsoft Presidio (`en_core_web_sm`) and compiled regex. Data is masked before model evaluation and re-hydrated prior to client delivery.
- **Stateful Human-in-the-Loop (HITL)**: Built-in state freezing via LangGraph's native `interrupt()` mechanism. Suspends execution dynamically for high-risk operations (e.g., prescriptions, record modifications) without session leaks.
- **Hierarchical Multi-Agent Supervisor Pattern**: A top-level supervisor orchestrating specialist sub-agents configured via `langchain.agents.create_agent` and exposed as tools:
  - **RAG Specialist**: Vector retrieval with internal policy checkpoints.
  - **Casual Chat Agent**: Low-latency conversational companion.
  - **Deep Research Agent (Upcoming)**: Multi-step web search and iterative synthesis.
  - **Knowledge Graph Agent (Upcoming)**: Relational entity-graph traversal.
- **Dockerized Storage**: Isolated, persistent vector database storage running via Docker Compose.
- **Laptop-Friendly Footprint**: Runs fully local on Apple Silicon / standard laptop CPUs with Ollama (`qwen2.5:7b`), lightweight spaCy models (~12 MB), and minimal RAM utilization (< 300 MB overhead).

---

## System Architecture

```
                              [User Prompt]
                                    │
                                    ▼
             ┌──────────────────────────────────────────────┐
             │         INPUT GUARDRAIL (In-Memory)          │
             │  - Regex Tokenizer (SSN, MRN, PID, Phone)    │
             │  - Presidio Analyzer + spaCy NER (Names)     │
             │  - Vault Hydration: <TOKEN_ID> ◄► Raw PII    │
             └──────────────────────┬───────────────────────┘
                                    │ (Sanitized State)
                                    ▼
             ┌──────────────────────────────────────────────┐
             │       SUPERVISOR AGENT (create_agent)        │
             │    Evaluates intent & routes to sub-agents   │
             └──────┬───────────────┼───────────────┬───────┘
                    │               │               │
    ┌───────────────┘               │               └───────────────┐
    ▼                               ▼                               ▼
┌──────────────────┐          ┌──────────────────┐            ┌──────────────────┐
│ chat_specialist  │          │  rag_specialist  │            │  (Future Agents) │
│ (create_agent)   │          │  (create_agent)  │            │  KG / Research   │
└─────────┬────────┘          └────────┬─────────┘            └────────┬─────────┘
│                            │                               │
│                   [Requires Review?]                       │
│               (High-risk action / policy)                  │
│                            │                               │
│                   ┌────────┴────────┐                      │
│                   │ YES: interrupt()│                      │
│                   │  (State Frozen) │                      │
│                   └────────┬────────┘                      │
│                            │                               │
│                   ┌────────┴────────┐                      │
│                   │ Human Operator  │                      │
│                   │ Approve / Edit  │                      │
│                   └────────┬────────┘                      │
│                            │                               │
│                   ┌────────┴────────┐                      │
│                   │ Query ChromaDB  │                      │
│                   │ (Docker Service)│                      │
│                   └────────┬────────┘                      │
│                            │                               │
└────────────────────────────┼───────────────────────────────┘
│
▼
┌──────────────────────────────────────────────┐
│        OUTPUT GUARDRAIL (In-Memory)          │
│  - Re-hydrates <TOKEN_ID> from Session Vault │
│  - Output sanity & schema validation         │
└──────────────────────┬───────────────────────┘
│
▼
[Final Response]

```

---

## Technology Stack

| Layer | Component | Version | Role |
| :--- | :--- | :--- | :--- |
| **Agent Orchestration** | [LangGraph](https://github.com/langchain-ai/langgraph) | `>=0.2.0` | Cyclic state graph engine, thread persistence, and interrupts |
| **Agent Factory** | [LangChain](https://github.com/langchain-ai/langchain) | `>=0.3.0` | Modern `create_agent` declarative agent scaffolding |
| **LLM Inference** | [Ollama](https://ollama.com/) / `langchain-ollama` | `>=0.2.0` | Local model runtime (`llama3.2:1b`, `qwen2.5`) |
| **PII/PHI Detection** | [Microsoft Presidio](https://github.com/microsoft/presidio) | `>=2.2.355` | Entity recognition and redaction pipeline |
| **Lightweight NER** | [spaCy](https://spacy.io/) (`en_core_web_sm`) | `>=3.7.4` | CPU-optimized (~12 MB) entity extractor for names/places |
| **Vector Storage** | [ChromaDB](https://hub.docker.com/r/chromadb/chroma) | `latest` | Containerized vector database running via Docker |
| **Tool Integrations** | DuckDuckGo, NetworkX | `>=6.0.0` | Search and knowledge-graph traversal |
| **Environment Management** | Python 3.12+, [`uv`](https://github.com/astral-sh/uv) | `latest` | Dependency resolution, virtual environments, runner |

---

## Project Structure

```text
agentic-rag-project/
├── .env                             # Active environment configuration
├── .env.example                     # Environment variables template
├── docker-compose.yaml              # Docker specification for ChromaDB
├── pyproject.toml                   # UV / Pip dependency manifest
├── README.md                        # Documentation
├── uv.lock                          # Pinned dependency lockfile
├── data/
│   ├── chromadb/                    # Docker volume mount for persistent vector records
│   └── raw/                         # Raw clinical and knowledge documents
├── src/
│   ├── __init__.py
│   ├── config.py                    # App configuration, thresholds, model settings
│   ├── main.py                      # Interactive runner & HITL execution loop
│   ├── agents/                      # Multi-agent implementations
│   │   ├── __init__.py
│   │   ├── supervisor.py            # Main router agent delegating to specialist tools
│   │   ├── chat_agent.py            # Conversational sub-agent tool
│   │   ├── rag_agent.py             # Knowledge retrieval sub-agent with HITL gate
│   │   ├── research_agent.py        # Multi-hop web search specialist (stub)
│   │   └── kg_agent.py              # Knowledge graph traversal specialist (stub)
│   ├── core/                        # Graph engine and state definitions
│   │   ├── __init__.py
│   │   ├── state.py                 # Global TypedDict schema & session vault
│   │   ├── graph.py                 # Graph assembly & node wiring
│   │   └── checkpointer.py          # In-memory persistence & checkpoint manager
│   ├── guardrails/                  # Bi-directional safety interceptors
│   │   ├── __init__.py
│   │   ├── presidio_engine.py       # Presidio analyzer initialization
│   │   ├── regex_patterns.py        # Custom patterns (MRN, Patient ID, etc.)
│   │   ├── input_guard.py           # Ingress interceptor (PII masking & vault storage)
│   │   └── output_guard.py          # Egress interceptor (PII re-hydration)
│   ├── hitl/                        # Human-in-the-loop policies
│   │   ├── __init__.py
│   │   ├── policies.py              # Risk evaluation rules & trigger criteria
│   │   └── actions.py               # Human review payload builder
│   ├── rag/                         # Document loaders and ingestion utilities
│   │   ├── __init__.py
│   │   └── retriever.py
│   └── tools/                       # Shared tool registry
│       ├── __init__.py
│       ├── retriever_tools.py       # ChromaDB HTTP client retrieval tool
│       ├── graph_tools.py           # NetworkX graph traversal interface
│       └── web_search_tools.py      # DuckDuckGo search integration
└── tests/
    ├── __init__.py
    ├── test_guardrails.py           # Verification of masking/unmasking roundtrip
    ├── test_hitl_workflow.py        # Verification of state pause and resume
    └── test_router.py               # Verification of supervisor intent routing

```

---

## Installation & Local Setup

### 1. Prerequisites

* **uv**: Recommended fast package manager.
```bash
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh

```


* **Docker & Docker Compose**: To host ChromaDB.
* **Ollama**: Local model engine.
```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text

```



### 2. Environment Setup

```bash
# Clone the repository
cd agentic-rag-project

# Sync dependencies with uv
uv sync --extra dev

# Download the lightweight NLP model for Presidio (< 15 MB)
uv run python -m spacy download en_core_web_sm

```

### 3. Start Database Containers

```bash
docker compose up -d

```

Verify ChromaDB container health:

```bash
docker ps

```

### 4. Configure Environment Variables

Create `.env` based on `.env.example`:

```env
# LLM Provider (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=qwen2.5:7b
EMBEDDING_MODEL=nomic-embed-text

# Docker ChromaDB Service
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Safety & HITL Thresholds
RETRIEVAL_CONFIDENCE_THRESHOLD=0.70
HITL_ENABLED=true

```

---

## Usage

### Interactive Demonstration

Run the main execution entrypoint to see casual chatting, automatic PII masking, and human-in-the-loop interruption in action:

```bash
uv run python src/main.py

```

Sample output:

```text
--- [User Prompt] (session_chat) ---
Hi, my name is John Doe and my phone is 555-0144. Just saying hello!

--- [Final Assistant Response] ---
Hello! It's nice to meet you, John. How can I assist you today?

--- [User Prompt] (session_rag_hitl) ---
Prescribe a dosage update for MRN-984210 based on our knowledge base.

[⏸️ HITL PAUSE] Execution paused by interrupt!
Review Payload: {'reason': 'High-risk medical query or document operation', 'flagged_content': 'Prescribe a dosage update for MRN-984210...', 'actions_available': ['approve', 'reject', 'override_response']}

[👨‍⚕️ Human Operator] Reviewing action... Status: APPROVED.

--- [Final Assistant Response] ---
Records for MRN-984210 do not currently indicate an active medication plan. Please verify the clinical details.

```

---

## Verification & Testing

Execute the automated test suite using `pytest`:

```bash
# Run all tests
uv run pytest -s tests/

# Test Guardrail Masking and De-masking roundtrip
uv run pytest -s tests/test_guardrails.py

# Test State Suspension and Resumption via interrupt()
uv run pytest -s tests/test_hitl_workflow.py

```

---

## Extending the Multi-Agent System

To attach a new specialist agent (e.g., `Research Agent` or `Knowledge Graph Agent`):

1. **Build the sub-agent using `create_agent**` in `src/agents/`:
```python
# src/agents/research_agent.py
from langchain.agents import create_agent
from langchain_core.tools import tool
from src.tools.web_search_tools import web_search
from src.config import settings

research_sub_agent = create_agent(
    model=llm,
    tools=[web_search],
    system_prompt="You are a deep research specialist. Synthesize search results."
)

@tool
def research_specialist(query: str) -> str:
    """Useful for multi-step web research and public fact-checking."""
    res = research_sub_agent.invoke({"messages": [{"role": "user", "content": query}]})
    return res["messages"][-1].content

```


2. **Register the tool in `src/agents/supervisor.py**`:
```python
from src.agents.research_agent import research_specialist

supervisor_agent = create_agent(
    model=llm,
    tools=[chat_specialist, rag_specialist, research_specialist],
    system_prompt="..."
)

```



---

## Security & Compliance Considerations

* **In-Memory Volatility**: The PII vault dictionary exists strictly in volatile RAM associated with the execution thread and is not stored in plaintext logs or database records.
* **De-identification Coverage**: Built to align with the HIPAA Safe Harbor De-identification standard (45 CFR § 164.514(b)(2)) by masking structured identifiers (SSN, MRN, phone, email) and unstructured named entities (names, healthcare facilities).

---

## Future Scope & Roadmap

* [ ] **Document Ingestion CLI**: Add automated chunking, metadata extraction, and vectorization for PDFs in `data/raw/`.
* [ ] **NetworkX Knowledge Graph Specialist**: Graph-RAG pipeline querying local entity relationships alongside vector search.
* [ ] **FastAPI & Reviewer Dashboard**: A lightweight review dashboard (FastAPI + Streamlit/React) allowing clinicians to approve/reject suspended threads visually.
* [ ] **Dynamic Model Fallback**: Automatic failover from local Ollama SLMs to managed cloud endpoints (OpenAI, Anthropic, Bedrock) when token context exceeds local thresholds.
