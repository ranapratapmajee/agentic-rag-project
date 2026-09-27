from backend.src.config import settings

def requires_human_review(query: str, low_confidence: bool = False) -> bool:
    """Evaluates whether an action requires human operator intervention."""
    if not settings.hitl_enabled:
        return False
    
    # Trigger 1: Explicit high-risk actions
    sensitive_keywords = ["prescribe", "delete_record", "modify_record", "dosage"]
    if any(keyword in query.lower() for keyword in sensitive_keywords):
        return True

    # Trigger 2: Unconfident or flagged retrieval
    if low_confidence:
        return True

    return False