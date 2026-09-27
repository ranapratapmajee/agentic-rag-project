from typing import Dict, Any
from langchain_core.messages import AIMessage
from backend.src.core.state import AgentState

def unmask_response(text: str, vault: Dict[str, str]) -> str:
    """Restores masked tokens back to original values."""
    if not vault:
        return text
    unmasked = text
    for token, original_val in vault.items():
        unmasked = unmasked.replace(token, original_val)
    return unmasked


def output_guardrail_node(state: AgentState) -> Dict[str, Any]:
    """LangGraph node wrapper for output re-hydration."""
    last_message = state["messages"][-1]
    text = str(last_message.content)
    vault = state.get("pii_vault") or {}

    unmasked_text = unmask_response(text, vault)

    return {"messages": [AIMessage(content=unmasked_text)]}