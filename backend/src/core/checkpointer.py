from langgraph.checkpoint.memory import InMemorySaver

def get_checkpointer() -> InMemorySaver:
    """Returns in-memory state checkpointer for session persistence and HITL interrupts."""
    return InMemorySaver()