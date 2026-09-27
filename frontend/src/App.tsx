import { AgentChat } from './components/agent-chat/AgentChat'

export default function App() {
  return (
    <div className="h-screen w-screen overflow-hidden bg-slate-950">
      <AgentChat
        config={{ apiBaseUrl: "http://localhost:8000" }}
        title="Clinical Multi-Agent Assistant"
        subtitle="Supervisor • RAG Specialist • Research Specialist"
      />
    </div>
  )
}