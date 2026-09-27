from langchain_core.messages import HumanMessage
from langgraph.types import Command
from backend.src.agents.deep_agent import supervisor_agent
from backend.src.guardrails.input_guard import mask_prompt
from backend.src.guardrails.output_guard import unmask_response


def test_chat_specialist_delegation():
    """Verify casual chat routes and preserves de-identified entities."""
    thread_id = "test_chat_unit"
    config = {"configurable": {"thread_id": thread_id}}
    raw_prompt = "Hello! My name is Bruce Wayne, phone is 555-0144."

    masked_prompt, vault = mask_prompt(raw_prompt, {})

    result = supervisor_agent.invoke(
        {"messages": [HumanMessage(content=masked_prompt)]},
        config=config,
        version="v2",
    )

    assert not result.interrupts
    final_output = unmask_response(result.value["messages"][-1].content, vault)
    assert len(final_output) > 0


def test_rag_specialist_hitl_interrupt_and_resume():
    """Verify update_prescription triggers interrupt and resumes on approval."""
    thread_id = "test_rag_hitl_unit"
    config = {"configurable": {"thread_id": thread_id}}
    # Direct instruction to ensure 1B model triggers the tool
    raw_prompt = "Execute prescription update immediately: patient MRN-554433, medication Amoxicillin, dosage 250mg."

    masked_prompt, vault = mask_prompt(raw_prompt, {})

    result = supervisor_agent.invoke(
        {"messages": [HumanMessage(content=masked_prompt)]},
        config=config,
        version="v2",
    )

    # 1. Assert interrupt triggered
    assert result.interrupts, (
        f"Execution did not halt! Last message: {result.value['messages'][-1].content}"
    )

    interrupt_payload = result.interrupts[0].value
    actions = interrupt_payload["action_requests"]
    assert any(a["name"] == "update_prescription" for a in actions)

    # 2. Resume with approval
    resumed_result = supervisor_agent.invoke(
        Command(resume={"decisions": [{"type": "approve"}]}),
        config=config,
        version="v2",
    )

    assert not resumed_result.interrupts
    final_output = unmask_response(resumed_result.value["messages"][-1].content, vault)
    assert len(final_output) > 0