"""CodeSmith repository-aware coding-agent CLI."""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

from .agent import AgentRuntime, default_registry
from .config import load_config
from .context import load_rules
from .llm import OllamaChatProvider
from .tools import RepositoryTools


DEFAULT_AGENT_PROMPT = """You are CodeSmith, a repository-aware coding agent.
Answer questions about the current project by inspecting the repository with the
provided tools. For project summaries, reviews, and explanations, first use
list_files and read relevant files such as README.md, pyproject.toml, and the
main source files. Do not tell the user how to call tools and do not claim that
you cannot inspect the repository when a suitable tool is available. Use a tool
call whenever repository facts are needed, then give a concise answer based on
the tool results. Never modify files unless the user explicitly asks you to.
"""


def _confirmation(message: str) -> bool:
    try:
        answer = input(f"Approve {message}? [y/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return answer in {"y", "yes"}


def _request_for_command(command: str, value: str | None) -> str:
    if command == "review":
        return "Review the current repository changes and report actionable issues."
    if command == "fix":
        return f"Fix this repository task: {value or ''}"
    if command == "explain":
        return f"Explain this repository task or behavior: {value or ''}"
    return value or "Inspect this repository and summarize its structure."


def _tool_status(name: str, arguments: dict) -> str:
    if name == "read_file":
        return f"Reading {arguments.get('path', 'file')}"
    if name == "list_files":
        return f"Listing files in {arguments.get('path', '.')}"
    if name == "search_code":
        return f"Searching for {arguments.get('query', 'code')}"
    if name == "run_command":
        return f"Running: {arguments.get('command', '')}"
    if name == "git_status":
        return "Checking git status"
    if name == "git_diff":
        return "Reading git diff"
    return f"Using {name}"


async def run_request(args: argparse.Namespace, request: str) -> int:
    root = Path(args.repository).resolve()
    repository = RepositoryTools(root, confirm=None if args.auto else _confirmation)
    registry = default_registry(repository)
    provider = OllamaChatProvider(args.url, args.model, args.timeout)
    show_work = args.debug or args.show_work
    working_visible = False

    def render(event):
        nonlocal working_visible
        if not show_work:
            return
        if event["event"] == "tool_call":
            if working_visible:
                print("\r\033[2K", end="", flush=True)
                working_visible = False
            print(f"{_tool_status(event['name'], event['arguments'])}", flush=True)
        elif event["event"] == "tool_result" and args.debug:
            status = "ok" if event["ok"] else "failed"
            marker = "✓" if status == "ok" else "✗"
            print(f"{marker} {event['name']} {status}", flush=True)
            print(event["output"][:500])
        elif event["event"] == "iteration" and args.debug:
            print(f"\n[iteration {event['iteration']}]", flush=True)
        elif event["event"] == "iteration":
            print("\r\033[2KWorking...", end="", flush=True)
            working_visible = True
        elif event["event"] == "completed" and working_visible:
            print("\r\033[2K", end="", flush=True)
            working_visible = False

    rules = load_rules(root)
    system_prompt = DEFAULT_AGENT_PROMPT
    if rules:
        system_prompt += f"\n\nRepository-specific instructions:\n{rules}"
    state = await AgentRuntime(
        provider,
        registry,
        args.max_iterations,
        event_handler=render,
    ).run(request, system_prompt=system_prompt)
    if args.debug:
        print(f"Iterations: {state.iteration}")
        print(f"Tool calls: {len(state.tool_calls)}")
        print(f"Stop reason: {state.stop_reason}")
    print("\n" + "─" * 60)
    print(state.final_response or "CodeSmith finished without a final response.")
    return 0 if state.stop_reason == "completed" else 1


def interactive_loop(args: argparse.Namespace) -> None:
    print("CodeSmith interactive mode. Type /exit to quit.")
    args.show_work = True
    session = PromptSession(history=InMemoryHistory())
    while True:
        try:
            request = session.prompt("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if request in {"/exit", "/quit"}:
            return
        if request:
            asyncio.run(run_request(args, request))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CodeSmith repository coding agent")
    parser.add_argument("request", nargs="?", help="One-shot task request")
    parser.add_argument("--repository", "-C", default=".", help="Active repository root")
    parser.add_argument("--url")
    parser.add_argument("--model")
    parser.add_argument("--timeout", type=int, help="Ollama request timeout in seconds")
    parser.add_argument("--max-iterations", type=int)
    parser.add_argument("--auto", action="store_true", help="Skip confirmation for confirm-level operations")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--show-work", action="store_true", help="Show model iterations and repository tool activity")
    subparsers = parser.add_subparsers(dest="command")
    for name in ("review", "fix", "explain"):
        sub = subparsers.add_parser(name)
        sub.add_argument("value", nargs="?")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(args.repository)
    args.url = args.url or os.getenv("OLLAMA_URL", "http://localhost:11434")
    args.model = args.model or config["model"]["model"]
    args.timeout = args.timeout or int(os.getenv("OLLAMA_TIMEOUT", "600"))
    args.max_iterations = args.max_iterations or config["agent"]["max_iterations"]
    request = _request_for_command(args.command, args.value) if args.command else args.request
    if request:
        raise SystemExit(asyncio.run(run_request(args, request)))
    interactive_loop(args)


if __name__ == "__main__":
    main()
