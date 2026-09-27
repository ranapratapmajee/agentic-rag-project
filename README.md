
# Clinical Deep Agents: Modular Agentic RAG with In-Memory Guardrails, Event Streaming & HITL

A privacy-first, enterprise-grade multi-agent clinical platform combining **Deep Agents (`create_deep_agent`)**, **LangChain / LangGraph Event Streaming (`version="v3"`)**, **Microsoft Presidio**, **Ollama**, and a modern **React + Vite** frontend.

The platform enforces strict clinical safety through bi-directional PII/PHI redaction, deterministic task delegation across specialist subagents, real-time token/tool event projection, and Human-in-the-Loop (**HITL**) approval gates before executing critical clinical tools (e.g., `update_prescription`).

---

## Key Features

* **Deep Agents v3 Event Streaming**: Consumes first-class `stream.subagents`, `stream.messages`, and `stream.tool_calls` projections over Server-Sent Events (SSE). UI cards render subagent lifecycle states and streaming tool deltas in real time without polluting conversation text.
* **Bi-Directional In-Memory Privacy Guardrails**: Zero-leakage tokenization of sensitive PII/PHI (HIPAA Safe Harbor, SSN, MRN, Patient ID, phone, email, names) using Microsoft Presidio and compiled regex. Data is tokenized into volatile memory vaults before LLM evaluation and re-hydrated prior to client delivery.
* **Human-in-the-Loop (HITL) Interruption & Resumption**: Execution halts deterministically using `interrupt_on` policies on sensitive tools (`update_prescription`). The system emits structured `interrupt` events to the frontend and resumes via `/chat/resume` with `approve`, `edit`, or `reject` decisions.
* **Multi-Agent Supervisor Pattern**:
* **Supervisor Dispatcher**: Handles direct pleasantries/chit-chat locally to eliminate latency hops, while deterministically routing clinical actions and deep queries to specialists.
* **RAG Specialist**: Clinical execution specialist querying knowledge bases and handling prescription updates with strict approval policies.
* **Research Specialist**: Multi-step web search agent synthesizing live external evidence.


* **Production React + Vite Frontend**: Modular, flat architecture (`src/components/agent-chat/`) with headless streaming state (`useAgentChat`), collapsible specialist tiles, live tool telemetry, and interactive HITL decision banners.
* **Local-First & Compute-Optimized**: Powered by local models running on Apple Silicon / CPU via `ChatOllama` with tiered token limits (`num_predict=128` for supervisor, `512` for specialists).

---

## System Architecture

```
                                  [User Message]
                                         │
                                         ▼
                      ┌────────────────────────────────────┐
                      │    INPUT GUARDRAIL (In-Memory)     │
                      │  - Regex Tokenizer (SSN, MRN, PID) │
                      │  - Presidio + spaCy NER (Names)    │
                      │  - Vault Hydration: <TOKEN_ID>     │
                      └──────────────────┬─────────────────┘
                                         │ (De-identified Prompt)
                                         ▼
                      ┌────────────────────────────────────┐
                      │    SUPERVISOR AGENT (Ollama)       │
                      │  - Direct replies for greetings    │
                      │  - Task delegation via `task` tool │
                      └───────┬────────────────────┬───────┘
                              │                    │
              ┌───────────────┘                    └───────────────┐
              ▼                                                    ▼
   ┌──────────────────────┐                             ┌──────────────────────┐
   │    rag-specialist    │                             │  research-specialist │
   │ (Clinical Execution) │                             │   (Web Retrieval)    │
   └──────────┬───────────┘                             └──────────┬───────────┘
              │                                                    │
     [Tool Invocation]                                      [web_search]
   update_prescription                                             │
              │                                                    ▼
     ┌────────┴────────┐                                ┌──────────────────────┐
     │  interrupt_on?  │                                │ Stream Tool Deltas   │
     └────────┬────────┘                                └──────────┬───────────┘
              │                                                    │
     ┌────────┴────────┐                                           │
     │ YES: Freeze Run │                                           │
     │  (Checkpointer) │                                           │
     └────────┬────────┘                                           │
              │                                                    │
              ▼                                                    │
    [SSE: Event 'interrupt']                                       │
              │                                                    │
    ┌─────────┴─────────┐                                          │
    │ Client Approval   │                                          │
    │ Approve/Edit/Deny │                                          │
    └─────────┬─────────┘                                          │
              │                                                    │
              ▼                                                    │
    [POST /chat/resume] ───────────────────────────────────────────┤
                                                                   │
                                                                   ▼
                                                ┌────────────────────────────────────┐
                                                │   OUTPUT GUARDRAIL (In-Memory)     │
                                                │  - Re-hydrates <TOKEN_ID> to Text  │
                                                │  - Safety & Output Validation      │
                                                └──────────────────┬─────────────────┘
                                                                   │
                                                                   ▼
                                                       [Client Browser (Vite/React)]

```

---

## Technology Stack

| Layer | Component | Version | Role |
| --- | --- | --- | --- |
| **Agent Orchestration** | [Deep Agents](https://github.com/langchain-ai?utm_source=gemini) / LangGraph | `>=0.1.0` / `>=0.2.0` | Hierarchical agent scaffolding with subagent projections and state freezing |
| **Streaming Protocol** | LangChain Event Streaming | `version="v3"` | Typed multi-channel stream (`messages`, `subagents`, `tool_calls`) |
| **Backend Web Framework** | [FastAPI](https://fastapi.tiangolo.com/?utm_source=gemini) | `>=0.110.0` | Asynchronous REST and Server-Sent Events (SSE) streaming API |
| **Frontend Framework** | [React](https://react.dev/?utm_source=gemini) + [Vite](https://vite.dev/?utm_source=gemini) + TypeScript | `React 19` / `Vite 6` | Production UI layer with custom headless streaming hooks |
| **Styling** | [Tailwind CSS](https://tailwindcss.com/?utm_source=gemini) | `v4` | High-contrast modern dark theme with elevation and status indicators |
| **LLM Inference** | [Ollama](https://ollama.com/?utm_source=gemini) / `langchain-ollama` | `>=0.2.0` | Local Apple Silicon Metal offload (`qwen2.5:7b` / custom models) |
| **PII/PHI Detection** | [Microsoft Presidio](https://github.com/microsoft/presidio?utm_source=gemini) + spaCy | `>=2.2.355` | Memory-vault de-identification pipeline |
| **Vector Storage** | [ChromaDB](https://hub.docker.com/r/chromadb/chroma?utm_source=gemini) | `latest` | Containerized vector database running via Docker Compose |
| **Package Management** | [`uv`](https://github.com/astral-sh/uv?utm_source=gemini) (Python) & `npm` (Node) | `latest` | High-speed dependency management for backend and frontend |

---

## Repository Structure

```text
clinical-agent-platform/
├── .gitignore
├── docker-compose.yaml                     # Persistent vector database service
├── README.md
│
├── backend/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── scripts/
│   │   └── chat_cli.py                     # Offline terminal debugging & testing
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_guardrails.py          # Input/output PII & safety verification
│   │   │   └── test_tools.py               # Unit tests for medical & search tools
│   │   └── integration/
│   │       ├── test_streamer.py            # Event stream projection integration test
│   │       └── test_interrupts.py          # HITL pause and resume verification
│   └── src/
│       ├── __init__.py
│       ├── config.py                       # Pydantic BaseSettings (Ollama, models, ports)
│       ├── main.py                         # FastAPI application factory, CORS & mounting
│       │
│       ├── api/                            # HTTP Transport Layer
│       │   ├── __init__.py
│       │   ├── deps.py                     # Dependency injection (checkpointers, security)
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── router.py               # Aggregated v1 route index
│       │       └── endpoints/
│       │           ├── __init__.py
│       │           └── chat.py             # POST /chat/stream & POST /chat/resume
│       │
│       ├── schemas/                        # Pydantic Data Transfer Objects (DTOs)
│       │   ├── __init__.py
│       │   └── chat.py                     # ChatRequest, DecisionRequest schemas
│       │
│       ├── agents/                         # Agent definitions & routing
│       │   ├── __init__.py
│       │   ├── specialists.py              # rag-specialist & research-specialist configs
│       │   └── supervisor.py               # Supervisor definition with create_deep_agent
│       │
│       ├── core/                           # Graph runtime & orchestration
│       │   ├── __init__.py
│       │   ├── checkpointer.py             # SQLite/Memory checkpointer for state pause
│       │   ├── state.py                    # Global state schemas
│       │   └── streamer.py                 # Async Deep Agents v3 SSE generator
│       │
│       ├── guardrails/                     # Security, privacy & clinical compliance
│       │   ├── __init__.py
│       │   ├── input_guard.py              # Ingress interceptor (PII masking to vault)
│       │   ├── output_guard.py             # Egress interceptor (PII re-hydration)
│       │   ├── presidio_engine.py          # Presidio Analyzer & Anonymizer engines
│       │   └── regex_patterns.py           # Clinical identifiers (MRN, SSN, Rx, PID)
│       │
│       ├── hitl/                           # Human-in-the-Loop policies
│       │   ├── __init__.py
│       │   ├── actions.py                  # State mutation helpers (approve, edit, reject)
│       │   └── policies.py                 # Policy verification rules
│       │
│       ├── rag/                            # Retrieval subsystem
│       │   ├── __init__.py
│       │   ├── embeddings.py               # Vector embedding models
│       │   └── retriever.py                # ChromaDB client & hybrid retrieval logic
│       │
│       └── tools/                          # Shared tools exposed to agents
│           ├── __init__.py
│           ├── medical.py                  # update_prescription & dosage modification
│           ├── retriever.py                # query_knowledge_base execution
│           └── search.py                   # web_search execution
│
└── frontend/
    ├── package.json
    ├── vite.config.ts                      # React + Tailwind CSS v4 Vite config
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx                        # Application mount entrypoint
        ├── App.tsx                         # Top-level viewport wrapper
        ├── index.css                       # Global CSS & Tailwind imports
        └── components/
            └── agent-chat/                 # Modular chat UI module
                ├── index.ts                # Barrel export
                ├── types.ts                # TypeScript stream event & message schemas
                ├── useAgentChat.ts         # Headless SSE engine & v3 event processor
                ├── AgentCards.tsx          # Subagent tiles, tool monitors & HITL banner
                └── AgentChat.tsx           # Assembled view with auto-scroll & inputs

```

---

## Installation & Setup

### 1. Prerequisites

* **Python 3.12+** and **[`uv`](https://astral.sh/uv?utm_source=gemini)**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

```


* **Node.js 20+** and `npm`
* **Docker & Docker Compose** (for vector storage)
* **Ollama**: Local model engine
```bash
ollama pull qwen2.5:7b
ollama pull nomic-embed-text

```



---

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment and sync dependencies
uv sync

# Download the lightweight NLP model for Presidio PII recognition
uv run python -m spacy download en_core_web_sm

# Start persistent storage containers
docker compose up -d

```

Create `backend/.env` (or configure via environment variables):

```env
# LLM Engine
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=qwen2.5:7b
EMBEDDING_MODEL=nomic-embed-text

# Storage & Services
CHROMA_HOST=localhost
CHROMA_PORT=8000

# App Settings
ENVIRONMENT=development
ALLOWED_ORIGINS=["http://localhost:5173"]
HITL_ENABLED=true

```

Run the backend API:

```bash
uv run uvicorn src.main:app --reload --port 8000

```

Backend Swagger UI will be available at: `http://localhost:8000/docs`

---

### 3. Frontend Setup

In a new terminal window:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev

```

The frontend application will be live at: `http://localhost:5173/`

---

## API Protocol: Event Streaming & HITL

The backend exposes two primary endpoints over HTTP / Server-Sent Events (SSE):

### 1. Initiate Stream (`POST /api/v1/chat/stream`)

**Request Payload:**

```json
{
  "thread_id": "session-user-101",
  "message": "Update prescription for patient MRN-984210 to Metformin 500mg."
}

```

**SSE Stream Events (`Content-Type: text/event-stream`):**

* **Token Delta**:
```json
data: {"event": "token", "source": "supervisor", "delta": "Delegating to clinical execution..."}

```


* **Subagent Status**:
```json
data: {"event": "subagent_status", "subagent": "rag-specialist", "status": "running"}

```


* **Tool Lifecycle**:
```json
data: {"event": "tool_start", "subagent": "rag-specialist", "tool": "update_prescription", "input": {"mrn": "MRN-984210", "dosage": "500mg"}}

```


* **Human-in-the-Loop Interruption**:
```json
data: {"event": "interrupt", "pending_tools": ["update_prescription"], "allowed_decisions": ["approve", "edit", "reject"]}

```



---

### 2. Resume Interrupted Stream (`POST /api/v1/chat/resume`)

When the user clicks **Approve**, **Edit**, or **Reject** in the frontend, the client resumes the frozen graph:

```json
{
  "thread_id": "session-user-101",
  "decision": "approve",
  "edited_args": null
}

```

*(If editing parameters, `edited_args` contains updated tool arguments to mutate the checkpointed state before execution).*

---

## Verification & Testing

Run all unit and integration tests with `pytest`:

```bash
cd backend

# Run the complete test suite
uv run pytest -v tests/

# Test in-memory PII masking/unmasking roundtrip
uv run pytest -v tests/unit/test_guardrails.py

# Test HITL interrupt detection and resumption
uv run pytest -v tests/integration/test_interrupts.py

```

---

## Security & Compliance Considerations

* **Volatile Vault Storage**: PII/PHI mappings (`<TOKEN_ID> ↔ Real Value`) are stored exclusively in volatile process memory isolated per request thread. Raw sensitive identifiers are never logged, forwarded to external models, or written to ChromaDB.
* **HIPAA Safe Harbor Alignment**: Designed to sanitize 18 HIPAA identifier categories (names, medical record numbers, dates, locations, phone numbers, SSNs) before agent reasoning.
* **Fail-Safe Clinical Guard**: The supervisor has no direct access to write/edit tools. All clinical modifications route through `rag-specialist` with mandatory human authorization checkpoints.