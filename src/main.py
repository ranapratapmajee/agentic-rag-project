from langchain_core.messages import HumanMessage
from langgraph.types import Command
from src.core.graph import app

def run_interaction(user_text: str, thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    print(f"\n--- [User Prompt] ({thread_id}) ---")
    print(user_text)

    # 1. Run the graph
    app.invoke(
        {
            "messages": [HumanMessage(content=user_text)],
            "pii_vault": {},
            "next_agent": None,
            "hitl_payload": None,
        },
        config=config,
    )

    # 2. Check if an interrupt paused execution
    current_state = app.get_state(config)
    if current_state.tasks and len(current_state.tasks[0].interrupts) > 0:
        interrupt_payload = current_state.tasks[0].interrupts[0].value
        print("\n[⏸️ HITL PAUSE] Execution paused by interrupt!")
        print("Review Payload:", interrupt_payload)

        # Simulate Human Approval
        print("\n[👨‍⚕️ Human Operator] Reviewing action... Status: APPROVED.")
        app.invoke(Command(resume={"approved": True}), config=config)

    # 3. Print the final response
    final_state = app.get_state(config)
    print("\n--- [Final Assistant Response] ---")
    print(final_state.values["messages"][-1].content)

if __name__ == "__main__":
    # Test 1: Casual conversation with PII masking
    run_interaction(
        user_text="Hi, my name is John Doe and my phone is 555-0144. Just saying hello!",
        thread_id="session_chat"
    )

    # Test 2: Medical query triggering HITL interrupt
    run_interaction(
        user_text="Prescribe a dosage update for MRN-984210 based on our knowledge base.",
        thread_id="session_rag_hitl"
    )