from typing import Dict, Any
from langchain_core.messages import HumanMessage
from src.core.state import AgentState
from src.guardrails.presidio_engine import presidio_analyzer

TARGET_ENTITIES = [
    "PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", 
    "US_SSN", "DATE_TIME", "MRN", "PATIENT_ID"
]

def input_guardrail_node(state: AgentState) -> Dict[str, Any]:
    """Intercepts user input, replaces sensitive data, and saves mapping in vault."""
    last_message = state["messages"][-1]
    raw_text = str(last_message.content)
    vault = dict(state.get("pii_vault") or {})

    # Detect entities
    results = presidio_analyzer.analyze(text=raw_text, entities=TARGET_ENTITIES, language="en")
    # Sort reverse by start index to avoid invalidating offsets
    sorted_results = sorted(results, key=lambda x: x.start, reverse=True)

    masked_text = raw_text
    counter = len(vault) + 1

    for item in sorted_results:
        raw_val = raw_text[item.start:item.end]
        token = f"<{item.entity_type}_{counter}>"
        vault[token] = raw_val
        masked_text = masked_text[:item.start] + token + masked_text[item.end:]
        counter += 1

    return {
        "messages": [HumanMessage(content=masked_text)],
        "pii_vault": vault
    }