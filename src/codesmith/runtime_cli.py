"""CodeSmith repository-aware coding-agent CLI."""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import shutil
import textwrap
from pathlib import Path

import requests
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.styles import Style

from .agent import AgentRuntime, default_registry
from .config import load_config
from .context import load_rules
from .llm import DEFAULT_MODEL, OpenRouterChatProvider, OpenRouterError
from .tools import RepositoryTools


FALLBACK_FREE_MODELS = [
    {
        "id": "openai/gpt-oss-20b:free",
        "name": "OpenAI: gpt-oss-20b (free)",
        "description": "Coding, reasoning, tool use, function calling, and structured outputs",
        "context": "131K",
    },
]
_FREE_MODELS_CACHE = None


DEFAULT_AGENT_PROMPT = """You are CodeSmith, a repository-aware coding agent.
Answer questions about the current project by inspecting the repository with the
provided tools. For project summaries, reviews, and explanations, first use
list_files and read relevant files such as README.md, pyproject.toml, and the
main source files. Do not tell the user how to call tools and do not claim that
you cannot inspect the repository when a suitable tool is available. Use a tool
call whenever repository facts are needed, then give a concise answer based on
the tool results. If the user asks to write, create, implement, or save code,
that is explicit permission to modify the repository: use write_file and create
a sensible filename when none is provided (for example, quick_sort.py for a
quick-sort request). After writing, confirm the exact file path and summarize
what was added. Do not modify files for questions, explanations, or reviews.
Format final answers for terminal readability: use a short heading, bullets for
multiple items, short paragraphs, and concise summaries.
"""


def _format_response(response: str) -> str:
    """Format model Markdown into a readable terminal response."""
    width = max(60, min(shutil.get_terminal_size((100, 24)).columns, 120))
    output = []
    in_code_block = False

    def style_inline(value: str) -> str:
        # ANSI styling keeps the CLI dependency-free and works in Docker and
        # regular terminals. Markdown markers themselves are not displayed.
        value = re.sub(r"(\*\*|__)(.*?)(\1)", r"\033[1m\2\033[0m", value)
        value = re.sub(r"(?<!`)`([^`]+)`(?!`)", r"\033[36m\1\033[0m", value)
        return value

    for raw_line in response.strip().splitlines():
        line = raw_line.rstrip()
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            if in_code_block:
                output.append("\033[2m┌─ code ─────────────────────────────────────┐\033[0m")
            else:
                output.append("\033[2m└───────────────────────────────────────────┘\033[0m")
            continue
        if in_code_block:
            output.append("\033[36m│ " + line + "\033[0m")
            continue
        if not line.strip():
            output.append(line)
            continue

        # Convert numbered Markdown lists into a consistent terminal bullet.
        line = re.sub(r"^\s*\d+[.)]\s+", "• ", line)
        if line.startswith("• ") or line.startswith("- ") or line.startswith("* "):
            bullet = "• "
            content = line[2:].strip()
            # Wrap the unstyled text so ANSI escape sequences do not affect
            # the line-length calculation.
            plain_content = re.sub(r"(\*\*|__|`)", "", content)
            wrapped = textwrap.wrap(plain_content, width=width - 4) or [""]
            output.append(bullet + style_inline(wrapped[0]))
            output.extend("  " + style_inline(part) for part in wrapped[1:])
        elif line.startswith("#"):
            output.append("\033[1m" + style_inline(line.lstrip("# ").strip()) + "\033[0m")
        else:
            output.extend(style_inline(part) for part in (textwrap.wrap(line, width=width) or [""]))

    return "\n".join(output).strip()


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


def _free_models(args: argparse.Namespace) -> list[dict]:
    """Load all currently free models from OpenRouter, with a safe fallback."""
    global _FREE_MODELS_CACHE
    if _FREE_MODELS_CACHE is not None:
        return _FREE_MODELS_CACHE
    try:
        response = requests.get(
            f"{args.url.rstrip('/')}/models",
            headers={"Authorization": f"Bearer {args.api_key}"},
            timeout=min(args.timeout, 30),
        )
        response.raise_for_status()
        models = []
        for model in response.json().get("data", []):
            model_id = model.get("id", "")
            pricing = model.get("pricing") or {}
            try:
                is_free = model_id.endswith(":free") or (
                    pricing and float(pricing.get("prompt", 1)) == 0
                    and float(pricing.get("completion", 1)) == 0
                )
            except (TypeError, ValueError):
                is_free = model_id.endswith(":free")
            if not is_free:
                continue
            parameters = model.get("supported_parameters") or []
            models.append({
                "id": model_id,
                "name": model.get("name") or model_id,
                "description": "Tool calling supported" if "tools" in parameters else "Free model",
                "context": _context_label(model.get("context_length")),
            })
        _FREE_MODELS_CACHE = sorted(models, key=lambda item: item["name"].lower())
    except (requests.exceptions.RequestException, ValueError, TypeError, KeyError):
        print("Could not fetch the OpenRouter model catalog; using the fallback list.")
        _FREE_MODELS_CACHE = FALLBACK_FREE_MODELS
    return _FREE_MODELS_CACHE


def _context_label(value) -> str:
    if not isinstance(value, (int, float)) or value <= 0:
        return "unknown"
    if value >= 1_000_000:
        return f"{value / 1_000_000:g}M"
    return f"{value / 1_000:g}K"


def _show_models(current_model: str, models: list[dict]) -> None:
    """Print all free models in a Codex-like picker."""
    print(f"\nAvailable free OpenRouter models ({len(models)}):\n")
    for index, model in enumerate(models, start=1):
        active = " (active)" if model["id"] == current_model else ""
        print(f"  {index}. {model['name']}{active}")
        print(f"     {model['id']}")
        print(f"     {model['description']} · {model['context']} context\n")


def _select_model(args: argparse.Namespace, session: PromptSession, request: str) -> None:
    """Show model suggestions and optionally select one for this session."""
    choice = request.partition(" ")[2].strip()
    models = _free_models(args)
    _show_models(args.model, models)
    if not choice:
        try:
            choice = session.prompt("Select a model (number, or Enter to cancel): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
    if not choice:
        print("Model unchanged.")
        return

    selected = None
    if choice.isdigit():
        index = int(choice) - 1
        if 0 <= index < len(models):
            selected = models[index]
    else:
        selected = next((model for model in models if model["id"] == choice), None)

    if selected is None:
        print("Unknown model selection. Choose one of the listed numbers or IDs.")
        return
    args.model = selected["id"]
    print(f"Selected model: {selected['name']} ({args.model})")


class _CommandCompleter(Completer):
    """Inline slash-command and model suggestions for the interactive prompt."""

    def __init__(self, models: list[dict]):
        self.models = models

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if not text.startswith("/"):
            return

        if " " not in text:
            commands = {
                "/models": "Browse and select an OpenRouter model",
                "/exit": "Exit CodeSmith",
                "/help": "Show interactive commands",
            }
            word = text
            for command, description in commands.items():
                if command.startswith(word):
                    yield Completion(
                        command,
                        start_position=-len(word),
                        display=command,
                        display_meta=description,
                    )
            return

        command, _, value = text.partition(" ")
        if command != "/models":
            return
        for model in self.models:
            if not value or model["id"].lower().startswith(value.lower()):
                yield Completion(
                    model["id"],
                    start_position=-len(value),
                    display=model["name"],
                    display_meta=model["description"],
                )


async def run_request(args: argparse.Namespace, request: str) -> int:
    root = Path(args.repository).resolve()
    repository = RepositoryTools(root, confirm=None if args.auto else _confirmation)
    registry = default_registry(repository)
    provider = OpenRouterChatProvider(args.api_key, args.model, args.timeout, args.url)
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
    try:
        state = await AgentRuntime(
            provider,
            registry,
            args.max_iterations,
            event_handler=render,
        ).run(request, system_prompt=system_prompt)
    except OpenRouterError as exc:
        if working_visible:
            print("\r\033[2K", end="", flush=True)
        print(f"\nOpenRouter request failed: {exc}")
        if "rate limit" in str(exc).lower() or "429" in str(exc):
            print("Free-model quota is exhausted. Wait for the reset or add OpenRouter credits.")
        else:
            print("Use /models and select a model marked 'Tool calling supported' for repository tasks.")
        return 1
    if args.debug:
        print(f"Iterations: {state.iteration}")
        print(f"Tool calls: {len(state.tool_calls)}")
        print(f"Stop reason: {state.stop_reason}")
    print("\n" + "─" * 60)
    print(_format_response(state.final_response or "CodeSmith finished without a final response."))
    return 0 if state.stop_reason == "completed" else 1


def interactive_loop(args: argparse.Namespace) -> None:
    print("CodeSmith · repository coding agent")
    print("Type /help for commands.\n")
    args.show_work = True
    models = _free_models(args)

    key_bindings = KeyBindings()

    @key_bindings.add("/")
    def _(event):
        """Open slash-command suggestions immediately after typing /."""
        event.current_buffer.insert_text("/")
        event.current_buffer.start_completion(select_first=True)

    @key_bindings.add("enter")
    def _(event):
        """Accept the first visible suggestion when Enter is pressed."""
        buffer = event.current_buffer
        state = buffer.complete_state
        if state and state.completions:
            completion = state.current_completion or state.completions[0]
            buffer.apply_completion(completion)
        buffer.validate_and_handle()

    style = Style.from_dict({
        # Legacy CodeSmith layout, recolored cyan.
        "completion-menu": "bg:#071923 #b8f4ff",
        "completion-menu.completion": "bg:#071923 #b8f4ff",
        "completion-menu.completion.current": "bg:#00a8c6 #001018 bold",
        "completion-menu.meta.completion": "bg:#071923 #ffffff",
        "completion-menu.meta.completion.current": "bg:#00a8c6 #ffffff",
        "scrollbar.background": "bg:#071923",
        "scrollbar.button": "bg:#00c8e8",
        "prompt": "#7defff bold",
        "bottom-toolbar": "bg:#071923 #b8f4ff",
    })

    def bottom_toolbar():
        return f" Model: {args.model}  ·  /models switch model  ·  /help  ·  /exit "

    session = PromptSession(
        history=FileHistory(str(Path.home() / ".codesmith_history")),
        completer=_CommandCompleter(models),
        key_bindings=key_bindings,
        complete_while_typing=True,
        complete_in_thread=False,
        mouse_support=False,
        style=style,
    )
    while True:
        try:
            request = session.prompt(
                FormattedText([("class:prompt", "➜ ")]),
                bottom_toolbar=bottom_toolbar,
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if request == "/exit":
            return
        if request == "/help":
            print("\nCommands:")
            print("  /models       Browse and select a free OpenRouter model")
            print("  /help         Show this help")
            print("  /exit         Exit CodeSmith\n")
            continue
        if request == "/models" or request.startswith("/models "):
            _select_model(args, session, request)
            continue
        if request:
            asyncio.run(run_request(args, request))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CodeSmith repository coding agent")
    parser.add_argument("request", nargs="?", help="One-shot task request")
    parser.add_argument("--repository", "-C", default=".", help="Active repository root")
    parser.add_argument("--url", help="OpenRouter API base URL")
    parser.add_argument("--api-key", help="OpenRouter API key (defaults to OPENROUTER_API_KEY)")
    parser.add_argument("--model")
    parser.add_argument("--timeout", type=int, help="OpenRouter request timeout in seconds")
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
    args.url = args.url or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    args.api_key = args.api_key or os.getenv("OPENROUTER_API_KEY")
    args.model = args.model or config["model"]["model"] or DEFAULT_MODEL
    args.timeout = args.timeout or int(os.getenv("OPENROUTER_TIMEOUT", "600"))
    args.max_iterations = args.max_iterations or config["agent"]["max_iterations"]
    request = _request_for_command(args.command, args.value) if args.command else args.request
    if request:
        raise SystemExit(asyncio.run(run_request(args, request)))
    interactive_loop(args)


if __name__ == "__main__":
    main()
