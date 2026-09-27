# Frontend Architecture & Integration Guide: Multi-Agent Chatbot

This document details the frontend architecture, protocol contracts, component responsibilities, and deployment steps for integrating with the **Deep Agents v3 Streaming Multi-Agent Supervisor** backend.

---

## 1. Architectural Overview

The frontend is structured around a **decoupled, event-driven streaming model**:

```
[ FastAPI Backend (Deep Agents v3) ]
                 │
                 │ Server-Sent Events (SSE) via /chat/stream & /chat/resume
                 ▼
      [ useAgentChat.ts (Engine) ]
                 │
                 ├── State Updates (Messages, Active Subagent, Tool Traces)
                 └── Interrupt State (Pause for Human Review)
                 │
        ┌────────┴────────┐
        ▼                 ▼
[ AgentChat.tsx ]  [ AgentCards.tsx ]
  (Message Feed)     (Subagent Cards, Tool Delays, Interrupt Modal)
```

### Core Design Principles
1. **Flat Modularity:** No deeply nested directories. All agent-specific logic lives inside `src/components/agent-chat/`.
2. **Headless Engine Separation:** `useAgentChat.ts` owns the network protocol and state transitions. UI components simply render state and trigger callbacks.
3. **Multi-Agent Awareness:** First-class rendering for subagents (`chat-specialist`, `rag-specialist`, `research-specialist`), tracking tool lifecycles without polluting the main assistant message bubble.
4. **Human-in-the-Loop (HITL) Support:** Halts message processing when the backend raises an interrupt for actions like `update_prescription`, surfacing approval or payload edits before resuming.

---

## 2. Directory & File Layout

Place this package inside your React/Vite project:

```text
frontend/
├── src/
│   ├── components/
│   │   └── agent-chat/
│   │       ├── types.ts          # Type contracts & SSE event schemas
│   │       ├── useAgentChat.ts   # Headless SSE parser & state machine
│   │       ├── AgentCards.tsx    # Subagent cards, tool views & HITL modal
│   │       └── AgentChat.tsx     # Chat shell, message feed & input bar
│   ├── App.tsx                   # Root entry point
│   ├── main.tsx                  # React DOM mount point
│   └── index.css                 # Base theme and font configuration
├── vite.config.ts                # Vite config (with Tailwind v4 plugin)
├── package.json
└── tsconfig.json
```

---

## 3. Data Contracts & SSE Event Protocol

The frontend consumes Server-Sent Events where each frame is a JSON string prefixed by `data: `:

### Event Types Received from Backend

| Event Name | Key Fields | Purpose |
| :--- | :--- | :--- |
| `token` | `source`, `delta` | Text chunks. If `source == "supervisor"`, streams to main response. If `source == subagent_name`, routes to that subagent. |
| `subagent_status` | `subagent`, `status` | Lifecycle status (`started`, `completed`, `failed`). Initializes subagent containers. |
| `tool_start` | `subagent`, `tool`, `input` | Triggered when a subagent starts executing a tool (e.g., `query_knowledge_base`). |
| `tool_delta` | `subagent`, `tool`, `delta` | Intermediate stream chunks from within the tool (e.g., retrieval logs or search progress). |
| `tool_end` | `subagent`, `tool`, `error` | Marks tool completion or logs failure reasons. |
| `interrupt` | `pending_tools`, `allowed_decisions` | Signals that execution has halted pending human verification. |

### Upstream Requests Sent to Backend

#### 1. Standard Query (`POST /chat/stream`)
```json
{
  "thread_id": "thread_abc123",
  "message": "Update prescription for patient PT-104 to Azithromycin 250mg"
}
```

#### 2. Interrupt Decision (`POST /chat/resume`)
```json
{
  "thread_id": "thread_abc123",
  "decision": "approve", // or "reject", "edit"
  "edited_args": {
    "dosage": "500mg"
  }
}
```

---

## 4. File-by-File Breakdown

### `types.ts`
Defines state models:
* `ToolCallState`: Lifecycle state, inputs, outputs, errors for a tool call.
* `SubagentState`: Maps subagent identity to its active status and dictionary of tool invocations.
* `ChatMessage`: Combines user/assistant role, content, and the map of subagents involved in the turn.
* `InterruptState`: Tools awaiting authorization and allowed decisions.

### `useAgentChat.ts`
* Reads HTTP chunk streams via `ReadableStreamDefaultReader` and `TextDecoder`.
* Buffers incoming chunks across `\n\n` boundaries.
* Emits state updates immutably to prevent race conditions during rapid token delivery.
* Exposes `messages`, `isStreaming`, `pendingInterrupt`, `sendMessage()`, and `resolveInterrupt()`.

### `AgentCards.tsx`
* **`SubagentCard`**: Displays specialized agent identity (`rag-specialist`, etc.), pulse indicator, and collapsible list of tools.
* **`ToolCallView`**: Displays parameters, streaming outputs, and execution status (`running`, `completed`, `error`).
* **`InterruptBanner`**: Warning card with `Approve`, `Edit Parameters`, and `Reject` buttons.

### `AgentChat.tsx`
* Main container with responsive scrolling.
* Top bar with connectivity/status indicator.
* Auto-scroll on new tokens or interrupt triggers.
* Textarea with keyboard handling (`Enter` to send, `Shift + Enter` for newlines).

---

## 5. Setup & Verification Steps

### 1. Prerequisites
* **Node.js** >= 18.x
* **npm** or **pnpm**

### 2. Dependency Installation
Inside `frontend/`:
```bash
npm install lucide-react
npm install -D tailwindcss @tailwindcss/vite
```

### 3. Vite & Tailwind Configuration
Verify `vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

Verify `src/index.css`:
```css
@import "tailwindcss";

body {
  margin: 0;
  padding: 0;
  background-color: #020617; /* slate-950 */
  color: #f8fafc;            /* slate-100 */
  -webkit-font-smoothing: antialiased;
}
```

### 4. Running the Dev Server
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`. Ensure your FastAPI backend is running on `http://localhost:8000` with CORS enabled for port 5173.

---

## 6. Next Steps & Future Fine-Tuning

When ready to refine the frontend further, consider:
1. **Markdown & Code Syntax Highlighting:** Add `react-markdown` and `rehype-highlight` for rendering tables and clinical formulas.
2. **Session Persistence:** Store `thread_id` and message history in `localStorage` or URL query params.
3. **Audio/Speech Input:** Integrate browser SpeechRecognition API for hands-free clinical notes.
4. **Export Artifacts:** Add an action to export conversation logs or updated prescription summaries as PDF/JSON.