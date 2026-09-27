import os
import sys
import time
import uuid
import threading
import itertools
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import FileHistory

# --- ANSI Typographic Styles ---
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


# =====================================================================
# 1. Generic Agent Protocol
# =====================================================================
class AgentInterface(ABC):
    @abstractmethod
    def run(self, user_prompt: str, thread_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def resume(self, decisions: List[Dict[str, Any]], thread_id: str) -> Dict[str, Any]:
        pass


# =====================================================================
# 2. Consistent In-Place Spinner
# =====================================================================
class Spinner:
    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str = "Thinking..."):
        self.message = message
        self._stop_event = threading.Event()
        self._thread = None
        self._start_time = None

    def _spin(self):
        spinner = itertools.cycle(self.FRAMES)
        sys.stdout.write("\033[?25l")  # Hide cursor
        sys.stdout.flush()

        while not self._stop_event.is_set():
            elapsed = int(time.time() - self._start_time)
            timer = f"{DIM}({elapsed}s){RESET}" if elapsed >= 2 else ""
            char = next(spinner)
            sys.stdout.write(f"\r  {char} {DIM}{self.message}{RESET} {timer}\033[K")
            sys.stdout.flush()
            time.sleep(0.07)

        # Clear line completely on exit and restore cursor
        sys.stdout.write("\r\033[K")
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    def __enter__(self):
        self._start_time = time.time()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()


# =====================================================================
# 3. Predictable-Spacing CLI Engine
# =====================================================================
class GenericAgentCLI:
    def __init__(self, agent: AgentInterface, banner: str = "AGENTIC ASSISTANT"):
        self.agent = agent
        self.banner = banner
        hist_file = os.path.expanduser("~/.agent_chat_history")
        self.history = FileHistory(hist_file)

    def _resolve_hitl(self, interrupts: List[Dict[str, Any]], thread_id: str) -> Dict[str, Any]:
        decisions = []
        for idx, item in enumerate(interrupts, 1):
            name = item.get("name", "Action Review")
            args = item.get("args", {})
            print(f"\n{BOLD}! HITL Review [{idx}/{len(interrupts)}]{RESET} › {name}")
            print(f"  {DIM}Arguments: {args}{RESET}\n")

            while True:
                choice = input(f"  Action [{BOLD}y{RESET}: approve / {BOLD}n{RESET}: reject / {BOLD}e{RESET}: edit] › ").strip().lower()
                if choice in ("y", "yes", ""):
                    decisions.append({"type": "approve"})
                    break
                elif choice in ("n", "no"):
                    reason = input(f"  {DIM}Rejection reason › {RESET}").strip() or "Rejected by operator."
                    decisions.append({"type": "reject", "message": reason})
                    break
                elif choice in ("e", "edit"):
                    edited = dict(args)
                    for k, v in args.items():
                        val = input(f"    {k} [{v}] › ").strip()
                        if val:
                            edited[k] = val
                    decisions.append({"type": "edit", "edited_action": {"name": name, "args": edited}})
                    break
                else:
                    print(f"  {DIM}Invalid option.{RESET}")

        print()  # Uniform gap before resume spinner
        with Spinner("Resuming..."):
            return self.agent.resume(decisions, thread_id)

    def start(self):
        thread_id = f"sess_{uuid.uuid4().hex[:6]}"

        print(f"\n{BOLD}{self.banner}{RESET}  {BOLD}·  session: {thread_id}{RESET}")
        print(f"{DIM}Commands: /exit to quit  ·  /reset to clear context{RESET}")
        print(f"{DIM}──────────────────────────────────────────────────────────{RESET}\n")

        while True:
            try:
                # 1. Prompt
                prompt_label = ANSI(f"{BOLD}You ›{RESET} ")
                user_input = prompt(prompt_label, history=self.history).strip()
                if not user_input:
                    continue

                if user_input in ("/exit", "/quit", "exit", "quit"):
                    print(f"\n{DIM}Session ended.{RESET}\n")
                    break

                if user_input == "/reset":
                    thread_id = f"sess_{uuid.uuid4().hex[:6]}"
                    print(f"\n{DIM}[Session reset · {thread_id}]{RESET}\n")
                    continue

                # 2. Add precisely 1 blank line below the user input line
                print()

                # 3. Run backend under the spinner
                with Spinner("Processing..."):
                    result = self.agent.run(user_input, thread_id)

                # 4. Handle HITL if triggered
                while result.get("interrupts"):
                    result = self._resolve_hitl(result["interrupts"], thread_id)

                # 5. Print assistant response with 1 blank line trailing before next prompt
                response_text = result.get("response", "").strip()
                print(f"{BOLD}Assistant ›{RESET} {response_text}\n")

            except (KeyboardInterrupt, EOFError):
                print(f"\n\n{DIM}Session ended.{RESET}\n")
                break
            except Exception as e:
                print(f"\n{BOLD}[Error]{RESET} {e}\n")


# =====================================================================
# 4. DeepAgent Adapter
# =====================================================================
class DeepAgentAdapter(AgentInterface):
    def __init__(self):
        from backend.src.agents.deep_agent import supervisor_agent
        from backend.src.guardrails.input_guard import mask_prompt
        from backend.src.guardrails.output_guard import unmask_response

        self.agent = supervisor_agent
        self.mask_fn = mask_prompt
        self.unmask_fn = unmask_response
        self.vaults: Dict[str, Dict[str, str]] = {}

    def _should_skip_ner(self, text: str) -> bool:
        return not any(c.isupper() or c.isdigit() or c in "@-_" for c in text)

    def _extract_final_text(self, out: Any, thread_id: str) -> str:
        messages = []
        if isinstance(out, dict):
            messages = out.get("messages", [])
        elif hasattr(out, "value") and isinstance(out.value, dict):
            messages = out.value.get("messages", [])

        for msg in reversed(messages):
            content = getattr(msg, "content", None)
            if content and not getattr(msg, "tool_calls", None):
                if isinstance(content, str) and content.strip():
                    return self.unmask_fn(content, self.vaults.get(thread_id, {}))
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            return self.unmask_fn(block.get("text", ""), self.vaults.get(thread_id, {}))

        return "No response generated."

    def _extract_interrupts(self, out: Any) -> List[Dict[str, Any]]:
        interrupts = getattr(out, "interrupts", None)
        if interrupts:
            val = interrupts[0].value
            return val.get("action_requests", [])
        return []

    def run(self, user_prompt: str, thread_id: str) -> Dict[str, Any]:
        vault = self.vaults.get(thread_id, {})
        if not self._should_skip_ner(user_prompt):
            masked_prompt, updated_vault = self.mask_fn(user_prompt, vault)
            self.vaults[thread_id] = updated_vault
            if masked_prompt != user_prompt:
                print(f"  {DIM}* [Guardrail]: PII masked{RESET}")
        else:
            masked_prompt = user_prompt

        from langchain_core.messages import HumanMessage
        config = {"configurable": {"thread_id": thread_id}}

        out = self.agent.invoke(
            {"messages": [HumanMessage(content=masked_prompt)]},
            config=config,
            version="v2",
        )

        return {
            "response": self._extract_final_text(out, thread_id),
            "interrupts": self._extract_interrupts(out),
        }

    def resume(self, decisions: List[Dict[str, Any]], thread_id: str) -> Dict[str, Any]:
        from langgraph.types import Command
        config = {"configurable": {"thread_id": thread_id}}

        out = self.agent.invoke(
            Command(resume={"decisions": decisions}),
            config=config,
            version="v2",
        )

        return {
            "response": self._extract_final_text(out, thread_id),
            "interrupts": self._extract_interrupts(out),
        }


if __name__ == "__main__":
    cli = GenericAgentCLI(agent=DeepAgentAdapter())
    cli.start()