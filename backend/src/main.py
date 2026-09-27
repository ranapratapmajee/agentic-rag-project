from typing import Literal, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.src.agents.deep_agent import supervisor_agent
from backend.src.core.streamer import generate_chat_stream

app = FastAPI(title="Deep Agents Multi-Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    thread_id: str
    message: str

class DecisionRequest(BaseModel):
    thread_id: str
    decision: Literal["approve", "edit", "reject"]
    edited_args: Optional[dict] = None

@app.post("/chat/stream")
async def chat_stream_endpoint(req: ChatRequest):
    return StreamingResponse(
        generate_chat_stream(user_message=req.message, thread_id=req.thread_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@app.post("/chat/resume")
async def resume_stream_endpoint(req: DecisionRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    state = await supervisor_agent.aget_state(config)
    
    if not state.next:
        raise HTTPException(status_code=400, detail="No pending interrupted state found.")

    if req.decision == "approve":
        pass
    elif req.decision == "edit" and req.edited_args:
        await supervisor_agent.aupdate_state(config, {"tool_inputs": req.edited_args})
    elif req.decision == "reject":
        await supervisor_agent.aupdate_state(config, {"tool_error": "User rejected the prescription update."})

    return StreamingResponse(
        generate_chat_stream(user_message=None, thread_id=req.thread_id, resume_decision={"status": req.decision}),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )