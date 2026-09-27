import asyncio
import json
from typing import AsyncGenerator, Optional
from langchain_core.messages import HumanMessage
from backend.src.agents.deep_agent import supervisor_agent

async def generate_chat_stream(
    user_message: Optional[str],
    thread_id: str,
    resume_decision: Optional[dict] = None,
) -> AsyncGenerator[str, None]:
    config = {"configurable": {"thread_id": thread_id}}
    queue: asyncio.Queue[str] = asyncio.Queue()

    input_payload = None if resume_decision else {"messages": [HumanMessage(content=user_message)]}

    # Open the v3 typed event stream
    stream = await supervisor_agent.astream_events(
        input_payload,
        config=config,
        version="v3"
    )

    async def consume_coordinator():
        async for message in stream.messages:
            async for delta in message.text:
                await queue.put(json.dumps({
                    "event": "token",
                    "source": "supervisor",
                    "delta": delta
                }))

    async def consume_subagents():
        async for subagent in stream.subagents:
            await queue.put(json.dumps({
                "event": "subagent_status",
                "subagent": subagent.name,
                "status": subagent.status
            }))

            async def subagent_tokens():
                async for msg in subagent.messages:
                    async for delta in msg.text:
                        await queue.put(json.dumps({
                            "event": "token",
                            "source": subagent.name,
                            "delta": delta
                        }))

            async def subagent_tools():
                async for call in subagent.tool_calls:
                    await queue.put(json.dumps({
                        "event": "tool_start",
                        "subagent": subagent.name,
                        "tool": call.tool_name,
                        "input": call.input
                    }))

                    async for delta in call.output_deltas:
                        await queue.put(json.dumps({
                            "event": "tool_delta",
                            "subagent": subagent.name,
                            "tool": call.tool_name,
                            "delta": delta
                        }))

                    await queue.put(json.dumps({
                        "event": "tool_end",
                        "subagent": subagent.name,
                        "tool": call.tool_name,
                        "error": call.error
                    }))

            await asyncio.gather(subagent_tokens(), subagent_tools())

    async def run_pipeline():
        try:
            await asyncio.gather(consume_coordinator(), consume_subagents())
        finally:
            await queue.put("__DONE__")

    producer_task = asyncio.create_task(run_pipeline())

    while True:
        payload = await queue.get()
        if payload == "__DONE__":
            break
        yield f"data: {payload}\n\n"

    await producer_task

    # Check for Human-In-The-Loop Interrupts
    state = await supervisor_agent.aget_state(config)
    if state.next:
        pending_tools = [task.name for task in state.tasks if hasattr(task, "name")]
        yield f"data: {json.dumps({'event': 'interrupt', 'pending_tools': pending_tools, 'allowed_decisions': ['approve', 'edit', 'reject']})}\n\n"