from typing import Annotated, List, Dict, Optional, Any
from typing_extensions import TypedDict
import operator
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """Global state shared across all agents and guardrail nodes."""
    # List of messages; operator.add ensures new messages append instead of overwrite
    messages: Annotated[List[BaseMessage], operator.add]
    
    # In-memory session vault for reversible de-identification: {"<PERSON_1>": "John Doe"}
    pii_vault: Dict[str, str]
    
    # Target specialist agent decided by supervisor
    next_agent: Optional[str]
    
    # Human-In-The-Loop metadata
    hitl_payload: Optional[Dict[str, Any]]