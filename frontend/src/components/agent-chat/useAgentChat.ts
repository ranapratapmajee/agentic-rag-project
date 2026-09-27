import { useState, useRef, useCallback } from "react";
import type { ChatMessage, InterruptState, DecisionType, AgentChatConfig } from "./types";

export function useAgentChat(config: AgentChatConfig = {}) {
    const { apiBaseUrl = "http://localhost:8000", threadId, headers, onError } = config;

    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isStreaming, setIsStreaming] = useState(false);
    const [pendingInterrupt, setPendingInterrupt] = useState<InterruptState | null>(null);
    const threadIdRef = useRef(threadId || `thread_${Date.now()}`);

    const processSSE = async (response: Response) => {
        if (!response.body) throw new Error("ReadableStream not available");
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const frames = buffer.split("\n\n");
                buffer = frames.pop() ?? "";

                for (const frame of frames) {
                    const line = frame.trim();
                    if (!line.startsWith("data: ")) continue;
                    const raw = line.slice(6).trim();
                    if (!raw || raw === "__DONE__") continue;

                    try {
                        const data = JSON.parse(raw);

                        // 1. Text deltas from supervisor or subagents
                        if (data.event === "token") {
                            setMessages((prev) => {
                                const list = [...prev];
                                const last = list[list.length - 1];
                                if (last && last.role === "assistant") {
                                    last.content += data.delta;
                                    last.activeSource = data.source;
                                }
                                return list;
                            });
                        }

                        // 2. Subagent lifecycle
                        else if (data.event === "subagent_status") {
                            setMessages((prev) => {
                                const list = [...prev];
                                const last = list[list.length - 1];
                                if (last && last.role === "assistant") {
                                    const currentSubagent = last.subagents?.[data.subagent] || {
                                        name: data.subagent,
                                        tools: {},
                                    };
                                    last.subagents = {
                                        ...last.subagents,
                                        [data.subagent]: { ...currentSubagent, status: data.status },
                                    };
                                }
                                return list;
                            });
                        }

                        // 3. Tool lifecycle (start, delta, end)
                        else if (data.event === "tool_start") {
                            setMessages((prev) => {
                                const list = [...prev];
                                const last = list[list.length - 1];
                                if (last && last.role === "assistant") {
                                    const subagents = { ...(last.subagents || {}) };
                                    const existingSub = subagents[data.subagent] || {
                                        name: data.subagent,
                                        status: "running",
                                        tools: {},
                                    };
                                    const existingTools = { ...(existingSub.tools || {}) };

                                    existingTools[data.tool] = {
                                        name: data.tool,
                                        input: data.input ?? null,
                                        status: "running",
                                        deltas: "",
                                    };

                                    subagents[data.subagent] = {
                                        ...existingSub,
                                        tools: existingTools,
                                    };

                                    last.subagents = subagents;
                                }
                                return list;
                            });
                        } else if (data.event === "tool_delta") {
                            setMessages((prev) => {
                                const list = [...prev];
                                const last = list[list.length - 1];
                                const tool = last?.subagents?.[data.subagent]?.tools?.[data.tool];
                                if (tool) {
                                    tool.deltas = (tool.deltas || "") + (data.delta || "");
                                }
                                return list;
                            });
                        } else if (data.event === "tool_end") {
                            setMessages((prev) => {
                                const list = [...prev];
                                const last = list[list.length - 1];
                                const tool = last?.subagents?.[data.subagent]?.tools?.[data.tool];
                                if (tool) {
                                    tool.status = data.error ? "error" : "completed";
                                    tool.error = data.error ?? null;
                                }
                                return list;
                            });
                        }

                        // 4. Human-in-the-loop interruption
                        else if (data.event === "interrupt") {
                            setPendingInterrupt(data);
                        }
                    } catch (e) {
                        console.error("Malformed SSE JSON:", raw, e);
                    }
                }
            }
        } finally {
            reader.releaseLock();
        }
    };

    const sendMessage = useCallback(
        async (content: string) => {
            if (!content.trim() || isStreaming) return;
            setIsStreaming(true);
            setPendingInterrupt(null);

            setMessages((prev) => [
                ...prev,
                { id: `usr_${Date.now()}`, role: "user", content },
                { id: `ast_${Date.now() + 1}`, role: "assistant", content: "", subagents: {} },
            ]);

            try {
                const res = await fetch(`${apiBaseUrl}/chat/stream`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", ...headers },
                    body: JSON.stringify({ thread_id: threadIdRef.current, message: content }),
                });
                if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
                await processSSE(res);
            } catch (err: any) {
                onError?.(err);
            } finally {
                setIsStreaming(false);
            }
        },
        [apiBaseUrl, headers, isStreaming, onError]
    );

    const resolveInterrupt = useCallback(
        async (decision: DecisionType, editedArgs?: Record<string, unknown>) => {
            if (!pendingInterrupt) return;
            setIsStreaming(true);
            setPendingInterrupt(null);

            try {
                const res = await fetch(`${apiBaseUrl}/chat/resume`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", ...headers },
                    body: JSON.stringify({
                        thread_id: threadIdRef.current,
                        decision,
                        edited_args: editedArgs,
                    }),
                });
                if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);
                await processSSE(res);
            } catch (err: any) {
                onError?.(err);
            } finally {
                setIsStreaming(false);
            }
        },
        [apiBaseUrl, headers, pendingInterrupt, onError]
    );

    return {
        messages,
        isStreaming,
        pendingInterrupt,
        sendMessage,
        resolveInterrupt,
        clearHistory: () => {
            setMessages([]);
            setPendingInterrupt(null);
            threadIdRef.current = `thread_${Date.now()}`;
        },
    };
}