from typing import Dict, Any

def build_review_payload(reason: str, prompt: str) -> Dict[str, Any]:
    """Prepares structured metadata for human reviewers."""
    return {
        "reason": reason,
        "flagged_content": prompt,
        "actions_available": ["approve", "reject", "override_response"]
    }