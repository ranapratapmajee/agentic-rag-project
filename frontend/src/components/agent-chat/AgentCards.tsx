import React, { useState } from "react";
import type { SubagentState, ToolCallState, InterruptState, DecisionType } from "./types";

export const ToolCallView: React.FC<{ tool: ToolCallState }> = ({ tool }) => {
    const [showDetails, setShowDetails] = useState(false);

    const statusBadge = {
        running: {
            bg: "bg-amber-500/10 border-amber-500/30 text-amber-300",
            dot: "bg-amber-400 animate-ping",
            label: "Executing",
        },
        completed: {
            bg: "bg-emerald-500/10 border-emerald-500/30 text-emerald-300",
            dot: "bg-emerald-400",
            label: "Completed",
        },
        error: {
            bg: "bg-rose-500/10 border-rose-500/30 text-rose-300",
            dot: "bg-rose-400",
            label: "Failed",
        },
    }[tool.status];

    return (
        <div className="rounded-lg border border-slate-700/80 bg-slate-900/90 p-2.5 font-mono text-xs shadow-inner">
            <div
                onClick={() => setShowDetails(!showDetails)}
                className="flex cursor-pointer items-center justify-between gap-2"
            >
                <div className="flex items-center gap-2 truncate">
                    <span className="text-slate-500">λ</span>
                    <span className="font-semibold text-indigo-300">{tool.name}</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-sans font-medium ${statusBadge.bg}`}>
                        <span className={`h-1.5 w-1.5 rounded-full ${statusBadge.dot}`} />
                        {statusBadge.label}
                    </span>
                    <span className="text-slate-500 text-[10px]">{showDetails ? "▲" : "▼"}</span>
                </div>
            </div>

            {showDetails && tool.input && (
                <div className="mt-2 border-t border-slate-800 pt-2">
                    <div className="text-[10px] uppercase tracking-wider text-slate-400 font-sans">Inputs:</div>
                    <pre className="mt-1 max-h-24 overflow-x-auto rounded bg-slate-950 p-2 text-[11px] text-slate-300">
                        {JSON.stringify(tool.input, null, 2)}
                    </pre>
                </div>
            )}

            {tool.deltas && (
                <div className="mt-2 border-t border-slate-800/80 pt-1.5 text-[11px] text-cyan-300/90">
                    <span className="text-slate-500 font-sans mr-1">Output:</span>
                    {tool.deltas}
                </div>
            )}

            {tool.error && (
                <div className="mt-1.5 text-[11px] text-rose-400 font-sans">
                    Error: {tool.error}
                </div>
            )}
        </div>
    );
};

export const SubagentCard: React.FC<{ subagent: SubagentState }> = ({ subagent }) => {
    const [collapsed, setCollapsed] = useState(false);
    const tools = Object.values(subagent.tools || {});

    const isRunning = subagent.status === "started" || subagent.status === "running";

    return (
        <div className="my-2 overflow-hidden rounded-xl border border-indigo-500/20 bg-gradient-to-b from-slate-900/90 to-slate-900/40 p-3 shadow-md backdrop-blur">
            <div
                onClick={() => setCollapsed(!collapsed)}
                className="flex cursor-pointer items-center justify-between font-sans text-xs"
            >
                <div className="flex items-center gap-2.5">
                    <div className="flex h-5 w-5 items-center justify-center rounded-md bg-indigo-500/20 text-indigo-300 text-[10px] font-bold">
                        AI
                    </div>
                    <span className="font-medium text-slate-200">{subagent.name}</span>
                    {isRunning && (
                        <span className="flex h-2 w-2 relative">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
                        </span>
                    )}
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-[10px] uppercase tracking-wider text-slate-400 font-mono">
                        {subagent.status}
                    </span>
                    <span className="text-slate-500 text-[10px]">{collapsed ? "▼" : "▲"}</span>
                </div>
            </div>

            {!collapsed && tools.length > 0 && (
                <div className="mt-2.5 space-y-2 border-t border-slate-800/80 pt-2">
                    {tools.map((t) => (
                        <ToolCallView key={t.name} tool={t} />
                    ))}
                </div>
            )}
        </div>
    );
};

export const InterruptBanner: React.FC<{
    interrupt: InterruptState;
    onDecision: (decision: DecisionType, editedArgs?: Record<string, unknown>) => void;
}> = ({ interrupt, onDecision }) => {
    const [showEdit, setShowEdit] = useState(false);
    const [jsonInput, setJsonInput] = useState("{}");

    return (
        <div className="my-4 rounded-xl border border-amber-500/40 bg-gradient-to-b from-amber-950/40 to-slate-900/90 p-4 shadow-xl backdrop-blur">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5 text-xs font-semibold text-amber-300">
                    <span className="flex h-2.5 w-2.5 relative">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
                        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500" />
                    </span>
                    Human Authorization Required
                </div>
                <span className="rounded bg-amber-500/20 px-2 py-0.5 font-mono text-[10px] text-amber-300">
                    Interrupted
                </span>
            </div>

            <p className="mt-2 text-xs text-slate-300 leading-relaxed">
                The agent paused execution to request approval for clinical tool:{" "}
                <span className="font-mono font-semibold text-amber-200 underline decoration-amber-500/50">
                    {interrupt.pending_tools.join(", ")}
                </span>
            </p>

            {showEdit && (
                <div className="mt-3">
                    <label className="text-[11px] text-slate-400 block mb-1">Edit Payload (JSON):</label>
                    <textarea
                        value={jsonInput}
                        onChange={(e) => setJsonInput(e.target.value)}
                        className="w-full rounded-lg border border-slate-700 bg-slate-950 p-2.5 font-mono text-xs text-slate-200 focus:border-amber-500 focus:outline-none"
                        rows={3}
                    />
                </div>
            )}

            <div className="mt-3.5 flex flex-wrap gap-2.5">
                <button
                    onClick={() => onDecision("approve")}
                    className="rounded-lg bg-emerald-600 px-4 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-emerald-500 transition active:scale-95"
                >
                    Approve Action
                </button>
                <button
                    onClick={() => {
                        if (!showEdit) {
                            setShowEdit(true);
                        } else {
                            try {
                                onDecision("edit", JSON.parse(jsonInput));
                            } catch {
                                alert("Invalid JSON format");
                            }
                        }
                    }}
                    className="rounded-lg bg-amber-600/90 px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-amber-500 transition active:scale-95"
                >
                    {showEdit ? "Submit Modified" : "Edit Parameters"}
                </button>
                <button
                    onClick={() => onDecision("reject")}
                    className="rounded-lg bg-rose-600/90 px-3.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-rose-500 transition active:scale-95"
                >
                    Reject
                </button>
            </div>
        </div>
    );
};