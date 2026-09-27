import re
from typing import Dict, Tuple, Any
from langchain_core.messages import HumanMessage
from backend.src.core.state import AgentState
from backend.src.guardrails.presidio_engine import presidio_analyzer

TARGET_ENTITIES = [
    "PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", 
    "US_SSN", "DATE_TIME", "MRN", "PATIENT_ID"
]

# Common tech/clinical words or acronyms that should NEVER be treated as PII
EXCLUDED_WORDS = {
    "rag", "llm", "api", "ai", "ml", "cli", "hitl", "nlp", "sql",
    "docker", "chroma", "chromadb", "ollama", "python", "vector",
    "gpu", "cpu", "ram", "rest", "json", "http", "https", "sdk",
    "mri", "ct", "ecg", "ekg", "icu", "ed", "iv", "prn", "po", "bid", "tid", "qid",
    "mg", "ml", "mcg", "meq", "kg", "lbs"
}

TITLE_PREFIXES = {"dr", "dr.", "doctor", "mr", "mr.", "mrs", "mrs.", "ms", "ms.", "patient"}

MONTHS_AND_DAYS = {
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "today", "yesterday", "tomorrow"
}


def is_valid_person(val: str, text: str, start: int) -> bool:
    """Verifies that an entity detected as PERSON is genuinely a human name."""
    clean_val = val.strip()
    words = clean_val.split()

    if clean_val.lower() in EXCLUDED_WORDS:
        return False

    # Single-word checks
    if len(words) == 1:
        # If all caps and 4 chars or less, it's an acronym, not a person
        if clean_val.isupper() and len(clean_val) <= 5:
            return False

        # Look at the preceding word to see if it's an honorific like Dr., Patient, etc.
        prefix_tokens = text[:start].strip().split()
        if prefix_tokens:
            last_prefix_word = prefix_tokens[-1].lower().rstrip(":")
            if last_prefix_word in TITLE_PREFIXES:
                return True

        # Isolated single words (e.g. "Docker", "What") are not valid person entities
        return False

    # Multi-word candidate (e.g. "John Doe", "Sarah Connor")
    return True


def is_valid_datetime(val: str) -> bool:
    """Rejects false-positive DATE_TIME entities like 'vector'."""
    clean = val.strip().lower()
    
    if clean in EXCLUDED_WORDS:
        return False

    # If it contains digits, it's a timestamp, year, or date (e.g., 2026, 09/12, 12:30)
    if any(c.isdigit() for c in clean):
        return True

    # Check if it's an explicit day of week or calendar month
    if any(m in clean for m in MONTHS_AND_DAYS):
        return True

    return False


def mask_prompt(text: str, vault: Dict[str, str]) -> Tuple[str, Dict[str, str]]:
    updated_vault = dict(vault) if vault else {}
    results = presidio_analyzer.analyze(text=text, entities=TARGET_ENTITIES, language="en")

    filtered_results = []
    for res in results:
        val = text[res.start:res.end].strip()

        # Reject false-positive PERSON entities
        if res.entity_type == "PERSON" and not is_valid_person(val, text, res.start):
            continue

        # Reject false-positive DATE_TIME entities
        if res.entity_type == "DATE_TIME" and not is_valid_datetime(val):
            continue

        filtered_results.append(res)

    sorted_results = sorted(filtered_results, key=lambda x: x.start, reverse=True)

    masked_text = text
    counter = len(updated_vault) + 1

    for res in sorted_results:
        raw_val = text[res.start:res.end]
        token = f"<{res.entity_type}_{counter}>"
        updated_vault[token] = raw_val
        masked_text = masked_text[:res.start] + token + masked_text[res.end:]
        counter += 1

    return masked_text, updated_vault


def input_guardrail_node(state: AgentState) -> Dict[str, Any]:
    last_message = state["messages"][-1]
    raw_text = str(last_message.content)
    vault = dict(state.get("pii_vault") or {})

    masked_text, updated_vault = mask_prompt(raw_text, vault)

    return {
        "messages": [HumanMessage(content=masked_text)],
        "pii_vault": updated_vault
    }