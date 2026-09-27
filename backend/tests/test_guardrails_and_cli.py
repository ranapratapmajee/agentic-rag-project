import pytest
from backend.src.guardrails.input_guard import mask_prompt
from backend.src.guardrails.output_guard import unmask_response


# =====================================================================
# 1. False Positive Guardrail Tests (Capital letters, Acronyms, Starts)
# =====================================================================

@pytest.mark.parametrize(
    "raw_input",
    [
        "what is RAG?",
        "What is RAG and how does it compare to an LLM?",
        "Explain how an API and SQL database work together in Docker.",
        "Can you describe the role of ChromaDB, CPU, and GPU in vector search?",
        "Please administer 500mg Metformin PO BID.",
        "Patient underwent an MRI and CT scan in the ICU.",
        "How do CLI interfaces handle HITL loops?",
    ],
)
def test_no_false_positive_masking(raw_input: str):
    """Verify tech acronyms, sentence starters, and clinical units are NOT masked as PERSON."""
    masked_text, vault = mask_prompt(raw_input, {})
    
    assert "<PERSON" not in masked_text, f"False positive PERSON detected in: {masked_text}"
    assert len(vault) == 0, f"Vault should be empty, but contained: {vault}"
    assert masked_text == raw_input


# =====================================================================
# 2. True Positive PII / PHI Masking Tests
# =====================================================================

@pytest.mark.parametrize(
    "raw_input,expected_token_types",
    [
        (
            "Patient John Doe arrived for consultation.",
            ["PERSON"],
        ),
        (
            "Contact Sarah Connor at sarah.connor@example.com immediately.",
            ["PERSON", "EMAIL_ADDRESS"],
        ),
        (
            "Patient MRN-887211 requires records review.",
            ["MRN"],
        ),
        (
            "Call doctor Gregory House at 555-0199 regarding Bruce Wayne.",
            ["PERSON"],
        ),
    ],
)
def test_true_positive_masking_and_vault(raw_input: str, expected_token_types: list[str]):
    """Verify actual sensitive entities are masked into tokens and recorded in the vault."""
    masked_text, vault = mask_prompt(raw_input, {})

    assert masked_text != raw_input
    assert len(vault) > 0

    # Ensure each expected entity type appears as a masked token
    for expected_type in expected_token_types:
        assert any(expected_type in token for token in vault.keys()), (
            f"Expected token type '{expected_type}' missing from vault keys: {list(vault.keys())}"
        )


# =====================================================================
# 3. Round-Trip Re-hydration (Masking -> Vault -> Unmasking)
# =====================================================================

def test_pii_roundtrip_integrity():
    """Verify that unmasking faithfully reconstructs the original sensitive values."""
    raw_prompt = "Patient Alice Walker (MRN-449102) was seen by Dr. Robert Smith."
    
    masked_prompt, vault = mask_prompt(raw_prompt, {})
    assert "Alice Walker" not in masked_prompt
    assert "Robert Smith" not in masked_prompt

    # Simulate an agent response that echoes back the tokens
    simulated_agent_reply = f"Summary for {list(vault.keys())[0]}: Follow up scheduled with {list(vault.keys())[-1]}."
    
    rehydrated_reply = unmask_response(simulated_agent_reply, vault)

    assert "<PERSON" not in rehydrated_reply
    assert "<MRN" not in rehydrated_reply
    # At least one of the original names must be restored
    assert ("Alice Walker" in rehydrated_reply) or ("Robert Smith" in rehydrated_reply)


# =====================================================================
# 4. Mixed Clinical & Tech Prompt Test
# =====================================================================

def test_mixed_acronym_and_real_pii():
    """Verify that in a prompt containing both RAG/LLM and real names, ONLY the names are masked."""
    mixed_prompt = "Can John Smith use RAG and LLM architecture with MRN-998822?"
    
    masked_prompt, vault = mask_prompt(mixed_prompt, {})

    # RAG and LLM must remain untouched
    assert "RAG" in masked_prompt
    assert "LLM" in masked_prompt
    
    # John Smith must be masked
    assert "John Smith" not in masked_prompt
    assert any("<PERSON" in token for token in vault.keys())

    # Full roundtrip verification
    restored = unmask_response(masked_prompt, vault)
    assert restored == mixed_prompt