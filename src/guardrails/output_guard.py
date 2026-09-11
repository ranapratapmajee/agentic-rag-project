from typing import Dict, Any
from langchain_core.messages import AIMessage
from src.core.state import AgentState

def output_guardrail_node(state: AgentState) -> Dict[str, Any]:
    """Rehydrates masked tokens in LLM output using the session vault."""
    last_message = state["messages"][-1]
    text = str(last_message.content)
    vault = state.get("pii_vault") or {}

    for token, original_val in vault.items():
        text = text.replace(token, original_val)

    return {"messages": [AIMessage(content=text)]}