"""CodeSmith repository-aware coding-agent CLI."""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from .agent import AgentRuntime, default_registry
from .config import load_config
from .context import load_rules
from .llm import OllamaChatProvider
from .tools import RepositoryTools


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


async def run_request(args: argparse.Namespace, request: str) -> int:
    root = Path(args.repository).resolve()
    repository = RepositoryTools(root, confirm=None if args.auto else _confirmation)
    registry = default_registry(repository)
    provider = OllamaChatProvider(args.url, args.model)

    def render(event):
        if not args.debug:
            return
        if event["event"] == "tool_call":
            print(f"[tool] {event['name']} {event['arguments']}")
        elif event["event"] == "tool_result":
            status = "ok" if event["ok"] else "failed"
            print(f"[tool:{status}] {event['name']}: {event['output'][:500]}")
        elif event["event"] == "iteration":
            print(f"[iteration {event['iteration']}]")

    rules = load_rules(root)
    state = await AgentRuntime(
        provider,
        registry,
        args.max_iterations,
        event_handler=render,
    ).run(request, system_prompt=rules or None)
    if args.debug:
        print(f"Iterations: {state.iteration}")
        print(f"Tool calls: {len(state.tool_calls)}")
        print(f"Stop reason: {state.stop_reason}")
    print(state.final_response or "CodeSmith finished without a final response.")
    return 0 if state.stop_reason == "completed" else 1


def interactive_loop(args: argparse.Namespace) -> None:
    print("CodeSmith interactive mode. Type /exit to quit.")
    while True:
        try:
            request = input("> ").strip()
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
    parser.add_argument("--max-iterations", type=int)
    parser.add_argument("--auto", action="store_true", help="Skip confirmation for confirm-level operations")
    parser.add_argument("--debug", action="store_true")
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
    args.max_iterations = args.max_iterations or config["agent"]["max_iterations"]
    request = _request_for_command(args.command, args.value) if args.command else args.request
    if request:
        raise SystemExit(asyncio.run(run_request(args, request)))
    interactive_loop(args)


if __name__ == "__main__":
    main()
