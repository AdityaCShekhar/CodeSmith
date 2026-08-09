#!/usr/bin/env python3
"""CLI tool similar to OpenAI Codex using local Ollama."""

import sys
import argparse
import traceback
import time
import os
import signal
import select
import re
import textwrap
from typing import Optional, List, Tuple
from pathlib import Path

try:
    import termios
    import tty
except ImportError:  # Windows
    termios = None
    tty = None

try:
    import msvcrt
except ImportError:  # macOS and Linux
    msvcrt = None

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys

try:
    from pygments import highlight
    from pygments.formatters import TerminalFormatter
    from pygments.lexers import TextLexer, get_lexer_by_name
except ImportError:
    highlight = None
    TerminalFormatter = None
    TextLexer = None
    get_lexer_by_name = None

try:
    from colorama import just_fix_windows_console
except ImportError:
    just_fix_windows_console = None

from .llm import OllamaClient, OllamaError
from .tools import FileTools, ContextInjector, ToolsError

try:
    import requests
except ImportError:
    # If requests isn't available, try to import urllib
    import urllib.request
    requests = None

if just_fix_windows_console is not None:
    just_fix_windows_console()

for output_stream in (sys.stdout, sys.stderr):
    if hasattr(output_stream, "reconfigure"):
        output_stream.reconfigure(errors="replace")

# ANSI color codes
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_CYAN = "\033[92m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"
COLOR_GRAY = "\033[90m"


# ============================================================================
# Initialization helpers
# ============================================================================

def wait_for_ollama(host: str = None, timeout: int = 120) -> bool:
    """Wait for Ollama to be ready (with extended timeout)."""
    host = host or os.getenv("OLLAMA_URL", "http://localhost:11434")
    print(f"⏳ Waiting for Ollama at {host}...")
    start = time.time()
    attempt = 0
    
    while time.time() - start < timeout:
        attempt += 1
        try:
            if requests:
                response = requests.get(f"{host}/api/tags", timeout=5)
                if response.status_code == 200:
                    print("✓ Ollama is ready")
                    return True
            else:
                # Fallback using urllib
                urllib.request.urlopen(f"{host}/api/tags", timeout=5)
                print("✓ Ollama is ready")
                return True
        except Exception as e:
            if attempt % 10 == 0:
                elapsed = int(time.time() - start)
                print(f"  Still waiting... ({elapsed}s elapsed)")
        time.sleep(1)
    
    print("❌ Ollama did not start in time")
    return False


def pull_model(model: str = "deepseek-coder:1.3b", host: str = None) -> bool:
    """Pull model if not already available."""
    host = host or os.getenv("OLLAMA_URL", "http://localhost:11434")
    try:
        print(f"\n📦 Checking for model: {model}")
        
        if not requests:
            print("⚠️  Cannot check model without requests library")
            print("   Starting CLI anyway - model may be pulling in background")
            return True
        
        # Check if model exists
        response = requests.get(f"{host}/api/tags", timeout=10)
        if response.status_code != 200:
            raise Exception(f"API returned {response.status_code}")
        
        models = response.json().get("models", [])
        model_names = [m.get("name", "") for m in models]
        
        # Check if our model is in the list
        if any(model in name for name in model_names):
            print(f"✓ Model '{model}' already available")
            print(f"  Available models: {', '.join(model_names)}")
            return True
        
        print(f"📥 Pulling {model}...")
        print(f"   (This may take 2-5 minutes on first run)")
        
        # Initiate model pull
        response = requests.post(
            f"{host}/api/pull",
            json={"name": model},
            timeout=600,
            stream=True
        )
        
        if response.status_code == 200:
            # Stream the pull progress
            for line in response.iter_lines():
                if line:
                    try:
                        import json
                        data = json.loads(line)
                        if "status" in data and "digest" in data:
                            status = data["status"]
                            if status in ["downloading", "verifying", "writing"]:
                                print(f"   {status}...", end="\r")
                    except:
                        pass
            print(f"✓ Model '{model}' ready               ")
            return True
        else:
            print(f"⚠️  Model pull returned status {response.status_code}")
            print("   Starting CLI anyway - model may be pulling in background")
            return True
            
    except requests.exceptions.Timeout:
        print("⚠️  Model pull timed out")
        print("   Starting CLI anyway - model may still be pulling")
        return True
    except Exception as e:
        print(f"⚠️  Could not verify/pull model: {e}")
        print("   Starting CLI anyway - model may be pulling in background")
        return True


def initialize_system(ollama_url: str = None, model: str = "deepseek-coder:1.3b") -> bool:
    """Initialize and prepare the system for CodeSmith.
    
    Args:
        ollama_url: URL of Ollama server
        model: Model to use
        
    Returns:
        True if initialization successful, False otherwise
    """
    print("\n" + "=" * 50)
    ollama_url = ollama_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
    print("🚀 CodeSmith Initialization")
    print("=" * 50)
    
    # Wait for Ollama (extended timeout)
    if not wait_for_ollama(ollama_url, timeout=120):
        print("❌ Cannot connect to Ollama after 2 minutes")
        print(f"   Make sure Ollama is running at {ollama_url}")
        return False
    
    # Pull model (but don't fail if we can't)
    pull_model(model=model, host=ollama_url)
    
    print("\n" + "=" * 50)
    print("✅ Ready! Starting CLI...")
    print("=" * 50 + "\n")
    return True


# ============================================================================
# Cross-platform streaming interrupt helper
# ============================================================================

class StreamInterruptor:
    """Detect Ctrl-C while streaming on Windows, macOS, and Linux."""
    
    def __init__(self):
        self.interrupted = False
        self.old_stdin_settings = None
    
    def start_monitoring(self):
        """Enable non-blocking key reads where the platform supports them."""
        if msvcrt is not None or termios is None or tty is None:
            return
        if not sys.stdin.isatty():
            return
        try:
            self.old_stdin_settings = termios.tcgetattr(sys.stdin.fileno())
            tty.setraw(sys.stdin.fileno())
        except (OSError, AttributeError):
            self.old_stdin_settings = None
    
    def stop_monitoring(self):
        """Restore terminal to normal mode."""
        if self.old_stdin_settings:
            try:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.old_stdin_settings)
            except (OSError, AttributeError):
                pass
            finally:
                self.old_stdin_settings = None
    
    def check_for_interrupt(self) -> bool:
        """Return True when Ctrl-C is pressed during streaming."""
        try:
            if msvcrt is not None:
                if not msvcrt.kbhit():
                    return False
                char = msvcrt.getwch()
                if char == "\x03":
                    self.interrupted = True
                    return True
                return False

            if self.old_stdin_settings is None:
                return False

            ready, _, _ = select.select([sys.stdin], [], [], 0)
            if ready:
                char = sys.stdin.read(1)
                if char == "\x03":
                    self.interrupted = True
                    return True
        except (OSError, ValueError, AttributeError):
            pass
        
        return False


class CodeSmithCLI:
    """CodeSmith CLI application for code generation with Ollama."""

    def __init__(
        self,
        ollama_url: str = None,
        model: str = "deepseek-coder:1.3b",
        stream: bool = True,
    ):
        """Initialize the CLI.
        
        Args:
            ollama_url: Ollama server URL
            model: Model to use for generation
        """
        self.ollama_url = ollama_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = model
        self.stream = stream
        self.client: Optional[OllamaClient] = None
        self.context_files = []
        self._init_client()

    def _init_client(self) -> None:
        """Initialize Ollama client with error handling."""
        try:
            self.client = OllamaClient(self.ollama_url, self.model)
            self._print_info(f"Connected to Ollama at {self.ollama_url}")
            self._print_info(f"Using model: {self.model}")
        except OllamaError as e:
            self._print_error(f"Failed to connect: {str(e)}")
            sys.exit(1)

    def _get_command_suggestions(self, partial: str = "") -> List[str]:
        """Get command suggestions for autocomplete."""
        all_commands = [
            "write", "models",
            "debug-files", "help", "exit"
        ]
        
        if not partial:
            return all_commands
        
        return [cmd for cmd in all_commands if cmd.startswith(partial)]

    def _get_files(self, partial: str = "") -> List[str]:
        """Get available files in current working directory."""
        try:
            # Search in the mounted current working directory
            workspace_paths = [
                Path("/work"),       # Current working directory mount
                Path("."),           # Current directory in container
                Path("/workspace"),  # Fallback to workspace
            ]
            
            workspace_dir = None
            for path in workspace_paths:
                if path.exists() and path.is_dir():
                    try:
                        # Make sure we can read it
                        list(path.iterdir())
                        workspace_dir = path
                        break
                    except (OSError, PermissionError):
                        continue
            
            if not workspace_dir:
                return []
            
            files = []
            skip_dirs = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache", ".docker", ".idea", "dist", "build", ".vscode", ".mypy_cache", ".env"}
            skip_extensions = {".pyc", ".pyo", ".so", ".egg-info"}
            skip_prefixes = {".", "~"}
            
            # Recursively find files with depth limit
            max_depth = 3
            
            def walk_dir(directory, current_depth=0):
                if current_depth > max_depth:
                    return
                try:
                    for item in sorted(directory.iterdir()):
                        try:
                            # Skip hidden items
                            if item.name.startswith("."):
                                continue
                            
                            # Skip certain directories
                            if item.is_dir() and item.name in skip_dirs:
                                continue
                            
                            if item.is_file():
                                # Skip certain file types
                                if item.suffix in skip_extensions:
                                    continue
                                
                                try:
                                    rel_path = str(item.relative_to(workspace_dir))
                                    # Fuzzy match - contains partial as substring
                                    if not partial or partial.lower() in rel_path.lower():
                                        files.append(rel_path)
                                except ValueError:
                                    pass
                            
                            elif item.is_dir() and current_depth < max_depth:
                                walk_dir(item, current_depth + 1)
                        except (OSError, PermissionError):
                            continue
                except (OSError, PermissionError):
                    pass
            
            walk_dir(workspace_dir)
            return sorted(set(files))[:20]  # Return top 20
        except Exception:
            return []

    def _get_command_descriptions(self) -> dict:
        """Get command descriptions for autocomplete display."""
        return {
            "write": "Generate code and save to file",
            "models": "List available models",
            "debug-files": "Show discovered files",
            "help": "Show full help",
            "exit": "Exit the application"
        }

    def _setup_prompt_session(self):
        """Setup prompt session with custom completer."""
        history_file = Path.home() / ".codesmith_history"
        key_bindings = KeyBindings()

        @key_bindings.add("/")
        def _(event):
            """Show command suggestions immediately after typing '/'. """
            if event.current_buffer.text:
                event.current_buffer.insert_text("/")
                return
            event.current_buffer.insert_text("/")
            event.current_buffer.start_completion(select_first=False)

        @key_bindings.add("@")
        def _(event):
            """Show file suggestions immediately after typing '@'."""
            buffer = event.current_buffer
            before_at = buffer.text
            if before_at and not before_at[-1].isspace():
                buffer.insert_text("@")
                return
            buffer.insert_text("@")
            buffer.start_completion(select_first=False)

        @key_bindings.add(Keys.Any)
        def _(event):
            """Keep slash-command completion active as the command is typed."""
            buffer = event.current_buffer
            buffer.insert_text(event.data)
            if buffer.text.startswith("/"):
                buffer.start_completion(select_first=False)
            elif "@" in buffer.text:
                last_at = buffer.text.rfind("@")
                if last_at == 0 or buffer.text[last_at - 1].isspace():
                    buffer.start_completion(select_first=False)
        
        # Dark forest-green CodeSmith theme for completion menus.
        style = Style.from_dict({
            'completion-menu': 'bg:#0d1f14 #b7f7c2',
            'completion-menu.completion': 'bg:#0d1f14 #b7f7c2',
            'completion-menu.completion.current': 'bg:#3fb950 #07140b bold',
            'completion-menu.meta.completion': 'bg:#0d1f14 #ffffff',
            'completion-menu.meta.completion.current': 'bg:#3fb950 #ffffff',
            'scrollbar.background': 'bg:#0d1f14',
            'scrollbar.button': 'bg:#3fb950',
            'prompt': '#98e6a5 bold',
        })
        
        class CommandCompleter(Completer):
            """Custom completer for CodeSmith commands."""
            def __init__(self, cli_instance):
                self.cli = cli_instance
            
            def get_completions(self, document: Document, complete_event):
                """Generate completions based on input."""
                text = document.text_before_cursor
                
                # Handle command suggestions with /
                if text.startswith("/"):
                    partial = text[1:].lower()
                    suggestions = self.cli._get_command_suggestions(partial)
                    descriptions = self.cli._get_command_descriptions()
                    
                    for cmd in suggestions:
                        yield Completion(
                            cmd + " ",
                            start_position=-len(partial),
                            display=f"/{cmd}",
                            display_meta=descriptions.get(cmd, "")
                        )
                
                # Handle file suggestions with @
                # Support @ anywhere in the line, not just at the start
                elif "@" in text:
                    # Find the last @ symbol
                    last_at_idx = text.rfind("@")
                    partial = text[last_at_idx + 1:]  # Text after @
                    search_partial = partial.lstrip('"')
                    
                    # Only show suggestions if there's a space or start of line before @
                    before_at = text[:last_at_idx]
                    is_valid_at = not before_at or before_at[-1] in (" ", "\t", "\n")
                    
                    if is_valid_at:
                        files = self.cli._get_files(search_partial)
                        
                        if files:  # Only yield if we have files
                            for filepath in files:
                                insertion = (
                                    f'"{filepath}"' if " " in filepath else filepath
                                )
                                yield Completion(
                                    insertion,
                                    start_position=-len(partial),
                                    display=f"  {filepath}",
                                    display_meta="Include in prompt"
                                )
        
        return PromptSession(
            completer=CommandCompleter(self),
            key_bindings=key_bindings,
            history=FileHistory(str(history_file)),
            enable_history_search=True,
            mouse_support=False,
            complete_while_typing=True,
            complete_in_thread=False,
            style=style,
        )

    def _print_info(self, message: str) -> None:
        """Print info message."""
        print(f"{COLOR_CYAN}ℹ {message}{COLOR_RESET}")

    def _print_success(self, message: str) -> None:
        """Print success message."""
        print(f"{COLOR_GREEN}✓ {message}{COLOR_RESET}")

    def _print_error(self, message: str) -> None:
        """Print error message."""
        print(f"\033[31m✗ {message}\033[0m")

    def _print_header(self, title: str) -> None:
        """Print formatted header."""
        print(f"\n{COLOR_BOLD}{COLOR_CYAN}━━ {title} ━━{COLOR_RESET}")

    def _format_code_block(self, code: str, language: str = "python") -> str:
        """Format code for display."""
        return f"\033[90m```{language}\n\033[0m{code}\033[90m\n```\033[0m"

    def _render_response(self, response: str) -> str:
        """Render Markdown code fences for a terminal-friendly response.

        Ollama returns Markdown frequently, but printing streamed tokens
        directly makes fences and indentation look broken. CodeSmith keeps
        the original response for callers and only formats the displayed
        version here.
        """
        if not response or "```" not in response:
            return response

        fence_pattern = re.compile(
            r"```([^\n`]*)\n?(.*?)```", flags=re.DOTALL
        )
        rendered_parts = []
        cursor = 0

        for match in fence_pattern.finditer(response):
            before = response[cursor:match.start()].strip()
            if before:
                rendered_parts.append(before)

            language = match.group(1).strip().split()[0] if match.group(1).strip() else "text"
            code = textwrap.dedent(match.group(2)).strip("\n")
            rendered_code = code

            if (
                highlight is not None
                and TerminalFormatter is not None
                and get_lexer_by_name is not None
                and sys.stdout.isatty()
            ):
                try:
                    lexer = get_lexer_by_name(language)
                except Exception:
                    lexer = TextLexer()
                rendered_code = highlight(
                    code,
                    lexer,
                    TerminalFormatter(),
                ).rstrip("\n")

            rendered_parts.append(
                f"{COLOR_GRAY}```{language}{COLOR_RESET}\n"
                f"{rendered_code}\n"
                f"{COLOR_GRAY}```{COLOR_RESET}"
            )
            cursor = match.end()

        trailing = response[cursor:].strip()
        if trailing:
            rendered_parts.append(trailing)

        return "\n\n".join(rendered_parts)

    @staticmethod
    def _extract_file_mentions(text: str) -> Tuple[List[str], str]:
        """Extract @file and @"file with spaces" mentions from text."""
        pattern = re.compile(r'@"([^"]+)"|@([^\s,;]+)')
        files = []
        for match in pattern.finditer(text):
            filepath = (match.group(1) or match.group(2)).rstrip(".!?:)]}")
            if filepath and filepath not in files:
                files.append(filepath)
        cleaned = pattern.sub("", text)
        cleaned = re.sub(r"[ \t]+", " ", cleaned).strip()
        return files, cleaned
    
    def _parse_file_requests(self, response: str) -> Tuple[List[str], bool]:
        """Parse intelligent file requests from AI response.
        
        Handles:
        - @filename (standard)
        - @filename.py (with extension)
        - @file1, @file2 (comma-separated)
        - @file1 and @file2 (and-separated)
        - @ with no filename (unclear - returns empty list with flag)
        
        Returns:
            tuple: (list of valid filenames, has_unclear_request)
        """
        valid_files = []
        unclear = False
        
        # Check for bare @ mentions (unclear requests)
        bare_mentions = re.findall(r'@\s*(?!["a-zA-Z0-9_./\\-])', response)
        if bare_mentions:
            unclear = True
            self._print_info("⚠️  Found unclear file request (@ with no filename) - need clarification")
        
        all_files, _ = self._extract_file_mentions(response)
        
        # Deduplicate and filter - check if files exist
        seen = set()
        for filename in all_files:
            if filename not in seen:
                seen.add(filename)
                # Basic file existence check - look for file in workspace
                try:
                    # Try to stat the file to see if it exists
                    from pathlib import Path
                    if Path(filename).exists() or Path(f"./{filename}").exists():
                        valid_files.append(filename)
                except:
                    # If file doesn't exist, include it anyway - let FileTools.read_file handle error
                    valid_files.append(filename)
        
        return list(dict.fromkeys(valid_files)), unclear  # Remove duplicates while preserving order

    def handle_generate(self, prompt: str, stream: bool = True) -> str:
        """Generate code from prompt.
        
        Args:
            prompt: User prompt
            stream: Whether to stream output
            
        Returns:
            Generated text
        """
        if not self.client:
            self._print_error("Client not initialized")
            return ""

        # Inject file context if any
        if self.context_files:
            prompt = ContextInjector.inject_files(prompt, self.context_files)

        self._print_header("Generating")
        self._print_info(f"Temperature: 0.7 | Top-p: 0.9")
        self._print_info("(Press Ctrl-C to interrupt)")

        try:
            if stream:
                interruptor = StreamInterruptor()
                interruptor.start_monitoring()
                result = ""
                
                try:
                    for token in self.client.generate(prompt, stream=True):
                        if interruptor.check_for_interrupt():
                            print("\n\n⚠️  Response interrupted by user (Ctrl-C)")
                            break
                        result += token
                    rendered = self._render_response(result)
                    if rendered:
                        print(rendered)
                finally:
                    interruptor.stop_monitoring()
                
                return result
            else:
                result = self.client.generate(prompt, stream=False)
                print(self._render_response(result))
                return result

        except KeyboardInterrupt:
            print("\n\n⚠️  Response interrupted by user (Ctrl-C)")
            return result if stream else ""
        except OllamaError as e:
            self._print_error(f"Generation failed: {str(e)}")
            return ""

    def handle_prompt_with_file_requests(self, prompt: str, stream: bool = True) -> str:
        """Generate a response and automatically load files requested by it.

        File requests are followed until the model no longer asks for a new
        existing file. There is intentionally no exchange-count limit.
        """
        current_prompt = prompt
        files_accessed = set(self.context_files)
        response = ""

        while True:
            response = self.handle_generate(current_prompt, stream=stream)
            if not response:
                return response

            requested_files, _ = self._parse_file_requests(response)
            new_files = [
                filepath for filepath in requested_files
                if filepath not in files_accessed
            ]

            files_loaded = []
            for filepath in new_files:
                try:
                    FileTools.read_file(filepath)
                    self.context_files.append(filepath)
                    files_accessed.add(filepath)
                    files_loaded.append(filepath)
                    self._print_success(f"Included @{filepath} in the prompt")
                except ToolsError as e:
                    self._print_error(f"Could not include @{filepath}: {e}")

            if not files_loaded:
                return response

            current_prompt = (
                "Continue answering the original request using the files now "
                "provided. Do not repeat the previous response.\n\n"
                f"Original request:\n{prompt}"
            )

    def handle_write(self, filepath: str) -> None:
        """Generate code from instructions and write it to a file.
        
        Args:
            filepath: Target file path
        """
        try:
            instruction = input(f"\033[1mInstructions for {filepath}:\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            self._print_info("Write cancelled")
            return

        if not instruction:
            self._print_error("Instructions cannot be empty")
            return

        prompt = (
            "You are a code-generation engine. Generate the complete contents "
            f"of the file '{filepath}'.\n\n"
            "STRICT OUTPUT RULES:\n"
            "1. Output only the final file contents.\n"
            "2. Do not write an explanation, introduction, summary, or notes.\n"
            "3. Do not use Markdown code fences such as ```python.\n"
            "4. Do not say what the code does before or after the code.\n"
            "5. Use minimal comments; include them only when essential for clarity.\n"
            "6. Never include commentary outside the code.\n"
            "7. Make the result directly usable as the requested file.\n\n"
            f"USER INSTRUCTIONS:\n{instruction}"
        )
        generated = self.handle_generate(prompt, stream=True).strip()

        # Models sometimes ignore the "code only" instruction and wrap code
        # in Markdown fences followed by an explanation. Save only the first
        # fenced block when one is present.
        import re
        import textwrap
        code_block = re.search(
            r"```(?:[a-zA-Z0-9_+#.-]+)?\s*(.*?)```",
            generated,
            flags=re.DOTALL,
        )
        content = textwrap.dedent(
            code_block.group(1) if code_block else generated
        ).strip()

        # Do not write common placeholder responses produced by weak models.
        if content.lower() in {"code", "your code here", "..."}:
            content = ""
        elif not code_block and re.search(
            r"(?i)\b(sure,? i can help|here(?:'s| is) the complete|i can help you)\b",
            content,
        ):
            content = ""

        if not content:
            self._print_error("No content generated; file was not written")
            return

        try:
            msg = FileTools.write_file(filepath, content)
            self._print_success(msg)
        except ToolsError as e:
            self._print_error(str(e))

    def handle_models(self) -> None:
        """List available models."""
        try:
            models = self.client.list_models()
            self._print_header("Available Models")
            for model in models:
                marker = "→" if model == self.model else " "
                print(f"  {marker} {model}")
            print()
        except OllamaError as e:
            self._print_error(str(e))

    def _show_command_suggestions(self) -> None:
        """Show quick command suggestions."""
        suggestions = f"""
\033[1mAvailable Commands:\033[0m
  \033[92m/write\033[0m <filename>     Generate code and save to file
  \033[92m/models\033[0m               List available models
  \033[92m/debug-files\033[0m         Show discovered files
  \033[92m/help\033[0m                 Show this help
  \033[92m/exit\033[0m                 Exit
"""
        print(suggestions)

    def print_help(self) -> None:
        """Print help message."""
        help_text = f"""
\033[1mCodeSmith - Code Generation CLI\033[0m

\033[1mCommands:\033[0m
  /write <filename>     Generate code from instructions and save it
  /models              List available models
  /debug-files          Show discovered files
  /help                Show this help
  /exit                Exit the application

\033[1mUsage:\033[0m
  Simply type your code generation prompts and press Enter.
  The AI will generate code based on your request.
  
\033[1mExample:\033[0m
  > Write a Python function to calculate factorial
  > Explain @utils.py and suggest improvements
  > /write output.py

"""
        print(help_text)

    def repl(self) -> None:
        """Run interactive REPL loop."""
        self._print_header("CodeSmith - Code Generation CLI")
        self._print_info("Type / then press Tab to see commands")
        self._print_info("Type @ to see files for context")
        self._print_info("Type /help for available commands")
        print()
        
        # Setup prompt session with autocomplete
        session = self._setup_prompt_session()

        try:
            while True:
                try:
                    # Get input with live suggestions
                    user_input = session.prompt(
                        FormattedText([("class:prompt", "➜ ")])
                    ).strip()

                    if not user_input:
                        continue

                    # Show suggestions if just "/"
                    if user_input == "/":
                        self._show_command_suggestions()
                        continue

                    # Handle commands
                    if user_input.startswith("/"):
                        parts = user_input.split(None, 1)
                        command = parts[0][1:]  # Remove the /
                        args = parts[1] if len(parts) > 1 else ""

                        if command == "exit":
                            self._print_info("Goodbye!")
                            break

                        elif command == "help":
                            self.print_help()

                        elif command == "write":
                            if args:
                                self.handle_write(args)
                            else:
                                self._print_error("Usage: /write <filename>")

                        elif command == "models":
                            self.handle_models()
                        
                        elif command == "debug-files":
                            # Debug command to show discovered files
                            workspace_paths = [
                                Path("/work"),
                                Path("."),
                                Path("/workspace"),
                            ]
                            
                            search_dir = None
                            for path in workspace_paths:
                                if path.exists():
                                    search_dir = path
                                    break
                            
                            self._print_info(f"Searching in: {search_dir}")
                            
                            files = self._get_files()
                            if files:
                                self._print_header("Available Files for @context")
                                for f in files[:15]:
                                    print(f"  @{f}")
                            else:
                                self._print_error("No files found in current directory")

                        else:
                            self._print_error(f"Unknown command: /{command}")

                    else:
                        files_mentioned, clean_prompt = self._extract_file_mentions(
                            user_input
                        )
                        original_context = self.context_files.copy()
                        try:
                            for filepath in files_mentioned:
                                if filepath not in self.context_files:
                                    try:
                                        FileTools.read_file(filepath)
                                        self.context_files.append(filepath)
                                        self._print_success(
                                            f"Included @{filepath} in this prompt"
                                        )
                                    except ToolsError as e:
                                        self._print_error(str(e))

                            if clean_prompt:
                                self.handle_prompt_with_file_requests(
                                    clean_prompt,
                                    stream=self.stream,
                                )
                        finally:
                            self.context_files = original_context

                except KeyboardInterrupt:
                    print()
                    self._print_info("Goodbye!")
                    break
                except EOFError:
                    self._print_info("Goodbye!")
                    break
                except Exception as e:
                    self._print_error(f"Unexpected error: {str(e)}")
                    traceback.print_exc()
        except KeyboardInterrupt:
            pass

    def run_single(self, prompt: str, stream: Optional[bool] = None) -> None:
        """Run a single generation and exit.
        
        Args:
            prompt: Input prompt
        """
        self.handle_generate(
            prompt,
            stream=self.stream if stream is None else stream,
        )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CodeSmith - Code generation CLI using Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --url http://localhost:11434 --model deepseek-coder:1.3b
  %(prog)s -p "Write a Python function to sort a list"
        """
    )

    parser.add_argument(
        "-u", "--url",
        default=os.getenv("OLLAMA_URL", "http://localhost:11434"),
        help="Ollama server URL (default: http://localhost:11434)"
    )

    parser.add_argument(
        "-m", "--model",
        default="deepseek-coder:1.3b",
        help="Model name (default: deepseek-coder:1.3b)"
    )

    parser.add_argument(
        "-p", "--prompt",
        help="Single prompt to execute and exit"
    )

    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming mode"
    )

    parser.add_argument(
        "--skip-init",
        action="store_true",
        help="Skip Ollama initialization (for advanced users)"
    )

    args = parser.parse_args()

    try:
        # Initialize system if not skipped
        if not args.skip_init:
            if not initialize_system(args.url, args.model):
                sys.exit(1)
        
        cli = CodeSmithCLI(
            ollama_url=args.url,
            model=args.model,
            stream=not args.no_stream,
        )

        if args.prompt:
            cli.run_single(args.prompt)
        else:
            cli.repl()

    except KeyboardInterrupt:
        print()
        print(f"{COLOR_CYAN}ℹ Goodbye!{COLOR_RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"{COLOR_RED}✗ Fatal error: {str(e)}{COLOR_RESET}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
