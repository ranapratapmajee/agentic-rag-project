import React, { useState, useRef, useEffect } from "react";
import { useAgentChat } from "./useAgentChat";
import { SubagentCard, InterruptBanner } from "./AgentCards";
import type { AgentChatConfig } from "./types";

export interface AgentChatProps {
    config?: AgentChatConfig;
    title?: string;
    subtitle?: string;
    placeholder?: string;
}

export function AgentChat({
    config,
    title = "Deep Agents Workspace",
    subtitle = "Clinical Dispatcher & Subagent Network",
    placeholder = "Message your clinical assistant...",
}: AgentChatProps) {
    const [input, setInput] = useState("");
    const { messages, isStreaming, pendingInterrupt, sendMessage, resolveInterrupt, clearHistory } = useAgentChat(config);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, pendingInterrupt]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isStreaming || pendingInterrupt) return;
        sendMessage(input);
        setInput("");
    };

    return (
        <div className="flex h-screen w-full flex-col bg-slate-950 text-slate-100 antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
            {/* Top Header Bar */}
            <header className="sticky top-0 z-20 flex items-center justify-between border-b border-slate-800/80 bg-slate-900/70 px-6 py-3.5 backdrop-blur-md">
                <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 text-white font-bold shadow-md shadow-indigo-500/20">
                        ⚕
                    </div>
                    <div>
                        <h1 className="text-sm font-semibold text-slate-100 tracking-tight flex items-center gap-2">
                            {title}
                            <span className="rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 text-[10px] font-normal text-emerald-400">
                                Online
                            </span>
                        </h1>
                        <p className="text-[11px] text-slate-400">{subtitle}</p>
                    </div>
                </div>

                <button
                    onClick={clearHistory}
                    className="rounded-lg border border-slate-700/70 bg-slate-800/50 px-2.5 py-1 text-xs text-slate-300 hover:bg-slate-800 hover:text-white transition"
                >
                    Clear
                </button>
            </header>

            {/* Message Feed Area */}
            <main className="flex-1 overflow-y-auto px-4 py-6 md:px-8 space-y-6">
                {messages.length === 0 && (
                    <div className="flex h-full flex-col items-center justify-center text-center p-6 text-slate-500">
                        <div className="h-12 w-12 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-xl text-slate-400 mb-3 shadow-inner">
                            💬
                        </div>
                        <h2 className="text-sm font-medium text-slate-300">No messages yet</h2>
                        <p className="text-xs text-slate-500 max-w-sm mt-1">
                            Ask a question, update a prescription, or delegate research across subagents.
                        </p>
                    </div>
                )}

                {messages.map((m) => {
                    const isUser = m.role === "user";
                    const subagents = Object.values(m.subagents || {});

                    return (
                        <div key={m.id} className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
                            {!isUser && (
                                <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-lg bg-indigo-950 border border-indigo-500/30 text-xs font-semibold text-indigo-300 shadow-sm">
                                    AG
                                </div>
                            )}

                            <div className={`max-w-[85%] md:max-w-[72%] flex flex-col ${isUser ? "items-end" : "items-start"}`}>
                                <div
                                    className={`rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-md ${isUser
                                            ? "bg-indigo-600 text-white font-normal rounded-tr-none"
                                            : "border border-slate-800 bg-slate-900/90 text-slate-200 rounded-tl-none"
                                        }`}
                                >
                                    {/* Nested Subagent Workflow Cards */}
                                    {!isUser && subagents.length > 0 && (
                                        <div className="mb-3 space-y-2">
                                            {subagents.map((s) => (
                                                <SubagentCard key={s.name} subagent={s} />
                                            ))}
                                        </div>
                                    )}

                                    {/* Assistant Text / Answer */}
                                    {m.content ? (
                                        <div className="whitespace-pre-wrap">{m.content}</div>
                                    ) : (
                                        !isUser && isStreaming && (
                                            <div className="flex items-center gap-1.5 py-1 text-xs text-slate-400 italic">
                                                <span className="h-1.5 w-1.5 rounded-full bg-indigo-400 animate-pulse" />
                                                Generating response...
                                            </div>
                                        )
                                    )}
                                </div>
                            </div>

                            {isUser && (
                                <div className="flex h-8 w-8 shrink-0 select-none items-center justify-center rounded-lg bg-slate-800 border border-slate-700 text-xs font-semibold text-slate-300">
                                    You
                                </div>
                            )}
                        </div>
                    );
                })}

                {/* Human-In-The-Loop Approval Banner */}
                {pendingInterrupt && (
                    <div className="max-w-2xl mx-auto">
                        <InterruptBanner interrupt={pendingInterrupt} onDecision={resolveInterrupt} />
                    </div>
                )}

                <div ref={bottomRef} />
            </main>

            {/* Input Form Bar */}
            <footer className="border-t border-slate-800/80 bg-slate-900/60 p-4 md:px-8 backdrop-blur-md">
                <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
                    <div className="relative flex items-center">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            disabled={isStreaming || !!pendingInterrupt}
                            placeholder={pendingInterrupt ? "Authorization required above..." : placeholder}
                            className="w-full rounded-2xl border border-slate-700/80 bg-slate-950/80 pl-4 pr-24 py-3 text-sm text-slate-100 placeholder-slate-500 shadow-inner focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
                        />
                        <button
                            type="submit"
                            disabled={isStreaming || !input.trim() || !!pendingInterrupt}
                            className="absolute right-2 rounded-xl bg-indigo-600 px-4 py-1.5 text-xs font-semibold text-white shadow hover:bg-indigo-500 disabled:opacity-40 transition active:scale-95"
                        >
                            {isStreaming ? (
                                <span className="flex items-center gap-1">
                                    <span className="h-2 w-2 rounded-full bg-white animate-spin" />
                                    Thinking
                                </span>
                            ) : (
                                "Send"
                            )}
                        </button>
                    </div>
                </form>
            </footer>
        </div>
    );
}