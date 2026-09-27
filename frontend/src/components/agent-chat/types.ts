export type DecisionType = "approve" | "edit" | "reject";

export interface ToolCallState {
    name: string;
    input: Record<string, unknown> | null;
    status: "running" | "completed" | "error";
    deltas: string;
    error?: string | null;
}

export interface SubagentState {
    name: string;
    status: "started" | "running" | "completed" | "failed" | "interrupted";
    tools: Record<string, ToolCallState>;
}

export interface ChatMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    activeSource?: string;
    subagents?: Record<string, SubagentState>;
}

export interface InterruptState {
    pending_tools: string[];
    allowed_decisions: DecisionType[];
}

export interface AgentChatConfig {
    apiBaseUrl?: string;
    threadId?: string;
    headers?: Record<string, string>;
    onError?: (err: Error) => void;
}