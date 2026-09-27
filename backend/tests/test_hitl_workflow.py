from langchain_core.messages import HumanMessage
from langgraph.types import Command
from backend.src.core.graph import app

def test_hitl_interrupt_and_resume():
    config = {"configurable": {"thread_id": "test_hitl_thread"}}
    prompt = "Please prescribe medication for patient with MRN-123456."

    # 1. First execution should hit interrupt()
    app.invoke(
        {
            "messages": [HumanMessage(content=prompt)],
            "pii_vault": {},
            "next_agent": None,
            "hitl_payload": None,
        },
        config=config,
    )

    state = app.get_state(config)
    assert len(state.tasks) > 0
    assert len(state.tasks[0].interrupts) > 0
    assert "High-risk" in state.tasks[0].interrupts[0].value["reason"]

    # 2. Resume execution with human operator decision
    app.invoke(Command(resume={"approved": True}), config=config)

    # 3. Verify execution finalized
    resumed_state = app.get_state(config)
    assert len(resumed_state.tasks) == 0
    final_msg = resumed_state.values["messages"][-1].content
    assert final_msg is not None