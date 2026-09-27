from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from backend.src.core.state import AgentState
from backend.src.core.checkpointer import get_checkpointer
from backend.src.guardrails.input_guard import input_guardrail_node
from backend.src.guardrails.output_guard import output_guardrail_node
from backend.src.agents.agent import supervisor_agent

def supervisor_node(state: AgentState) -> Dict[str, Any]:
    """Invokes the supervisor agent with the sanitized conversation state."""
    # supervisor_agent delegates to sub-agent tools (chat_specialist, rag_specialist)
    result = supervisor_agent.invoke({"messages": state["messages"]})
    return {
        "messages": [result["messages"][-1]]
    }

# Build the main state graph
builder = StateGraph(AgentState)

# Add nodes
builder.add_node("input_guard", input_guardrail_node)
builder.add_node("supervisor", supervisor_node)
builder.add_node("output_guard", output_guardrail_node)

# Define linear pipeline
builder.add_edge(START, "input_guard")
builder.add_edge("input_guard", "supervisor")
builder.add_edge("supervisor", "output_guard")
builder.add_edge("output_guard", END)

# Compile with in-memory checkpointer for thread persistence & HITL interrupts
checkpointer = get_checkpointer()
app = builder.compile(checkpointer=checkpointer)