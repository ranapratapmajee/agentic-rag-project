from backend.src.core.state import AgentState
from backend.src.guardrails.input_guard import input_guardrail_node
from backend.src.guardrails.output_guard import output_guardrail_node
from langchain_core.messages import HumanMessage, AIMessage

def test_guardrail_masking_and_unmasking():
    original_prompt = "Schedule consultation for Alice Smith with phone 555-432-1098 and MRN-102938."
    state: AgentState = {
        "messages": [HumanMessage(content=original_prompt)],
        "pii_vault": {},
        "next_agent": None,
        "hitl_payload": None,
    }

    # 1. Masking
    masked_state = input_guardrail_node(state)
    masked_text = masked_state["messages"][0].content
    vault = masked_state["pii_vault"]

    assert "Alice Smith" not in masked_text
    assert "555-432-1098" not in masked_text
    assert "MRN-102938" not in masked_text
    assert len(vault) >= 3

    # 2. Simulated model response referencing the masked token
    token = list(vault.keys())[0]
    llm_draft = AIMessage(content=f"Confirmed consultation for {token}.")
    
    # 3. Unmasking
    restored_state = output_guardrail_node({
        "messages": [llm_draft],
        "pii_vault": vault,
        "next_agent": None,
        "hitl_payload": None,
    })
    final_output = restored_state["messages"][0].content

    assert any(name in final_output for name in ["Alice Smith", "555-432-1098", "MRN-102938"])
    print("\n[Passed] Masked text:", masked_text)
    print("[Passed] Unmasked output:", final_output)