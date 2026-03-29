#!/usr/bin/env python3
"""CLI tool similar to OpenAI Codex using local Ollama."""

import sys
import argparse
import traceback
import time
import os
import signal
import termios
import tty
import select
from typing import Optional, List
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style

from llm import OllamaClient, OllamaError
from tools import FileTools, ShellTools, ContextInjector, ToolsError

try:
    import requests
except ImportError:
    # If requests isn't available, try to import urllib
    import urllib.request
    requests = None

# ANSI color codes
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_CYAN = "\033[36m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"
COLOR_GRAY = "\033[90m"


# ============================================================================
# Initialization Functions (migrated from init.py)
# ============================================================================

def wait_for_ollama(host: str = "http://ollama:11434", timeout: int = 120) -> bool:
    """Wait for Ollama to be ready (with extended timeout)."""
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


def pull_model(model: str = "deepseek-coder:1.3b", host: str = "http://ollama:11434") -> bool:
    """Pull model if not already available."""
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


def initialize_system(ollama_url: str = "http://ollama:11434", model: str = "deepseek-coder:1.3b") -> bool:
    """Initialize and prepare the system for DeepX.
    
    Args:
        ollama_url: URL of Ollama server
        model: Model to use
        
    Returns:
        True if initialization successful, False otherwise
    """
    print("\n" + "=" * 50)
    print("🚀 DeepX Initialization")
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
# Streaming Helper with ESC Interrupt
# ============================================================================

class StreamInterruptor:
    """Helper to detect ESC key during streaming."""
    
    def __init__(self):
        self.interrupted = False
        self.old_stdin_settings = None
    
    def start_monitoring(self):
        """Set terminal to raw mode for ESC detection."""
        try:
            self.old_stdin_settings = termios.tcgetattr(sys.stdin.fileno())
            tty.setraw(sys.stdin.fileno())
        except (termios.error, AttributeError):
            # Non-interactive terminal or not available
            pass
    
    def stop_monitoring(self):
        """Restore terminal to normal mode."""
        if self.old_stdin_settings:
            try:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.old_stdin_settings)
            except (termios.error, AttributeError):
                pass
    
    def check_for_esc(self) -> bool:
        """Check if ESC key was pressed. Returns True if interrupted."""
        try:
            # Check if there's input available without blocking
            ready, _, _ = select.select([sys.stdin], [], [], 0)
            
            if ready:
                char = sys.stdin.read(1)
                # ESC key is ASCII 27
                if ord(char) == 27:
                    self.interrupted = True
                    return True
        except (OSError, termios.error):
            pass
        
        return False


class DeepXCLI:
    """CLI application for code generation with Ollama."""

    def __init__(self, ollama_url: str = "http://ollama:11434", model: str = "deepseek-coder:1.3b"):
        """Initialize the CLI.
        
        Args:
            ollama_url: Ollama server URL
            model: Model to use for generation
        """
        self.ollama_url = ollama_url
        self.model = model
        self.client: Optional[OllamaClient] = None
        self.context_files = []
        self.qa_conversation = []  # Store Q&A history
        self.qa_turn_count = 0  # Track number of exchanges
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
            "read", "write", "run", "context", "models", "help", "exit"
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
            "read": "View file contents",
            "write": "Save code to file",
            "run": "Execute shell command",
            "context": "Manage file context",
            "models": "List available models",
            "help": "Show full help",
            "exit": "Exit the application"
        }

    def _setup_prompt_session(self):
        """Setup prompt session with custom completer."""
        history_file = Path.home() / ".deepx_history"
        
        # Style that matches terminal theme
        style = Style.from_dict({
            'completion-menu': 'bg:#333333 #cccccc',
            'completion-menu.completion': '#cccccc',
            'completion-menu.completion.current': 'bg:#0066ff #ffffff bold',
        })
        
        class CommandCompleter(Completer):
            """Custom completer for DeepX commands."""
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
                            display_meta=descriptions.get(cmd, "")
                        )
                
                # Handle file suggestions with @
                # Support @ anywhere in the line, not just at the start
                elif "@" in text:
                    # Find the last @ symbol
                    last_at_idx = text.rfind("@")
                    partial = text[last_at_idx + 1:]  # Text after @
                    
                    # Only show suggestions if there's a space or start of line before @
                    before_at = text[:last_at_idx]
                    is_valid_at = not before_at or before_at[-1] in (" ", "\t", "\n")
                    
                    if is_valid_at:
                        files = self.cli._get_files(partial)
                        
                        if files:  # Only yield if we have files
                            for filepath in files:
                                yield Completion(
                                    filepath,
                                    start_position=-len(partial),
                                    display_meta="Add to context"
                                )
        
        return PromptSession(
            completer=CommandCompleter(self),
            history=FileHistory(str(history_file)),
            enable_history_search=True,
            mouse_support=False,
            complete_while_typing=True,
            style=style,
        )

    def _print_info(self, message: str) -> None:
        """Print info message."""
        print(f"\033[36mℹ {message}\033[0m")

    def _print_success(self, message: str) -> None:
        """Print success message."""
        print(f"\033[32m✓ {message}\033[0m")

    def _print_error(self, message: str) -> None:
        """Print error message."""
        print(f"\033[31m✗ {message}\033[0m")

    def _print_header(self, title: str) -> None:
        """Print formatted header."""
        print(f"\n\033[1m\033[36m━━ {title} ━━\033[0m")

    def _format_code_block(self, code: str, language: str = "python") -> str:
        """Format code for display."""
        return f"\033[90m```{language}\n\033[0m{code}\033[90m\n```\033[0m"

    def handle_qa_conversation(self, initial_prompt: str) -> None:
        """Handle automated multi-turn Q&A conversation.
        
        DeepSeek automatically gets requested files without user intervention.
        Limited to 3 exchanges to prevent infinite loops.
        
        Args:
            initial_prompt: Initial user question
        """
        import re
        MAX_TURNS = 3
        self.qa_turn_count = 0
        self.qa_conversation = []
        
        current_prompt = initial_prompt
        files_accessed = set()
        
        while self.qa_turn_count < MAX_TURNS:
            self.qa_turn_count += 1
            
            # Build conversation context
            conversation_history = "\n".join([
                f"[{item['type'].upper()}] {item['content'][:150]}..." 
                if len(item['content']) > 150 else f"[{item['type'].upper()}] {item['content']}"
                for item in self.qa_conversation
            ])
            
            # System instruction for file requests
            system_msg = """You are a code analysis assistant. When you need more context to answer better, 
ask for it like: "I need to see @filename.py" or "Can you show me @other_file.py?". Be direct."""
            
            if conversation_history:
                enhanced_prompt = f"{system_msg}\n\nContext:\n{conversation_history}\n\n{current_prompt}"
            else:
                enhanced_prompt = f"{system_msg}\n\n{current_prompt}"
            
            self._print_header(f"Exchange {self.qa_turn_count}/{MAX_TURNS}")
            self._print_info("(Press ESC to interrupt)")
            
            # Get response from DeepSeek
            try:
                interruptor = StreamInterruptor()
                interruptor.start_monitoring()
                response = ""
                
                try:
                    for token in self.client.generate(enhanced_prompt, stream=True):
                        if interruptor.check_for_esc():
                            print("\n⚠️  Response interrupted by user (ESC)")
                            interruptor.interrupted = True
                            break
                        response += token
                        print(token, end="", flush=True)
                    print("\n")  # Newline after streaming
                finally:
                    interruptor.stop_monitoring()
                
                if not response or interruptor.interrupted:
                    self._print_info("Conversation ended by user")
                    break
                
                self.qa_conversation.append({
                    "type": "assistant",
                    "content": response
                })
                
            except OllamaError as e:
                self._print_error(f"Generation failed: {str(e)}")
                break
            
            # Detect file requests
            file_requests = re.findall(r'@([\w\-_.]+)', response)
            new_files = [f for f in set(file_requests) if f not in files_accessed]
            
            if new_files and self.qa_turn_count < MAX_TURNS:
                # Automatically load requested files
                files_loaded = []
                for filename in new_files:
                    try:
                        content = FileTools.read_file(filename)
                        self.qa_conversation.append({
                            "type": "context",
                            "content": f"@{filename}:\n{content}"
                        })
                        files_accessed.add(filename)
                        files_loaded.append(filename)
                        self._print_success(f"✓ Loaded @{filename}")
                    except ToolsError as e:
                        self._print_error(f"✗ Could not read @{filename}")
                
                if files_loaded:
                    print()
                    current_prompt = "Continue analyzing with the files I provided above."
                    continue
            
            # If still exchanges left and no file request, ask for follow-up
            if self.qa_turn_count < MAX_TURNS:
                print()
                follow_up = input("Your question (or press Enter to exit): ").strip()
                
                if not follow_up:
                    break
                
                self.qa_conversation.append({
                    "type": "user",
                    "content": follow_up
                })
                current_prompt = follow_up
            else:
                break
        
        self._print_info(f"Q&A session ended ({self.qa_turn_count}/{MAX_TURNS} exchanges)")
        self.qa_conversation = []
        self.qa_turn_count = 0

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
        self._print_info("(Press ESC to interrupt)")

        try:
            if stream:
                interruptor = StreamInterruptor()
                interruptor.start_monitoring()
                result = ""
                
                try:
                    for token in self.client.generate(prompt, stream=True):
                        if interruptor.check_for_esc():
                            print("\n\n⚠️  Response interrupted by user (ESC)")
                            break
                        result += token
                        print(token, end="", flush=True)
                    print()  # Newline after streaming
                finally:
                    interruptor.stop_monitoring()
                
                return result
            else:
                result = self.client.generate(prompt, stream=False)
                print(result)
                return result

        except OllamaError as e:
            self._print_error(f"Generation failed: {str(e)}")
            return ""

    def handle_write(self, filepath: str) -> None:
        """Write content to file.
        
        Args:
            filepath: Target file path
        """
        print(f"\033[1mEnter content (Ctrl+D to save):\033[0m")
        lines = []
        try:
            while True:
                lines.append(input())
        except EOFError:
            pass

        content = "\n".join(lines)

        try:
            msg = FileTools.write_file(filepath, content)
            self._print_success(msg)
        except ToolsError as e:
            self._print_error(str(e))

    def handle_read(self, filepath: str) -> None:
        """Read and display file content.
        
        Args:
            filepath: File path to read
        """
        try:
            content = FileTools.read_file(filepath)
            self._print_header(f"Reading {filepath}")
            print(content)
            print()
        except ToolsError as e:
            self._print_error(str(e))

    def handle_run(self, command: str) -> None:
        """Run shell command.
        
        Args:
            command: Command to execute
        """
        self._print_header(f"Running: {command}")
        try:
            output = ShellTools.safe_command(command)
            print(output)
            print()
        except ToolsError as e:
            self._print_error(str(e))

    def handle_context(self, args: list) -> None:
        """Manage context files.
        
        Args:
            args: Command arguments
        """
        if not args:
            if self.context_files:
                self._print_info("Current context files:")
                for i, f in enumerate(self.context_files, 1):
                    print(f"  {i}. {f}")
            else:
                self._print_info("No context files set")
            return

        action = args[0]
        if action == "add":
            filepath = " ".join(args[1:])
            try:
                FileTools.read_file(filepath)  # Verify file exists
                self.context_files.append(filepath)
                self._print_success(f"Added {filepath} to context")
            except ToolsError as e:
                self._print_error(str(e))

        elif action == "remove":
            try:
                idx = int(args[1]) - 1
                removed = self.context_files.pop(idx)
                self._print_success(f"Removed {removed} from context")
            except (ValueError, IndexError):
                self._print_error("Invalid index")

        elif action == "clear":
            self.context_files = []
            self._print_success("Context cleared")

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
  \033[36m/write\033[0m <filename>     Save code to file
  \033[36m/read\033[0m <filename>      View file contents
  \033[36m/run\033[0m <command>        Execute shell command
  \033[36m/context\033[0m              Manage file context
  \033[36m/models\033[0m               List available models
  \033[36m/help\033[0m                 Show this help
  \033[36m/exit\033[0m                 Exit
"""
        print(suggestions)

    def print_help(self) -> None:
        """Print help message."""
        help_text = f"""
\033[1mDeepX - Code Generation CLI\033[0m

\033[1mCommands:\033[0m
  /write <filename>     Write input to file
  /read <filename>      Read and display file
  /run <command>        Execute shell command
  /context add <file>   Add file to context
  /context remove <n>   Remove context file by number
  /context              Show current context
  /models              List available models
  /help                Show this help
  /exit                Exit the application

\033[1mUsage:\033[0m
  Simply type your code generation prompts and press Enter.
  The AI will generate code based on your request.
  
\033[1mExample:\033[0m
  > Write a Python function to calculate factorial
  > /context add utils.py
  > /read utils.py
  > /write output.py

"""
        print(help_text)

    def repl(self) -> None:
        """Run interactive REPL loop."""
        self._print_header("DeepX - Code Generation CLI")
        self._print_info("Type / then press Tab to see commands")
        self._print_info("Type @ then press Tab to see files for context")
        self._print_info("Type /help for available commands")
        print()
        
        # Setup prompt session with autocomplete
        session = self._setup_prompt_session()

        try:
            while True:
                try:
                    # Get input with live suggestions
                    user_input = session.prompt(FormattedText([("bold", "> ")])).strip()

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

                        elif command == "read":
                            if args:
                                self.handle_read(args)
                            else:
                                self._print_error("Usage: /read <filename>")

                        elif command == "write":
                            if args:
                                self.handle_write(args)
                            else:
                                self._print_error("Usage: /write <filename>")

                        elif command == "run":
                            if args:
                                self.handle_run(args)
                            else:
                                self._print_error("Usage: /run <command>")

                        elif command == "context":
                            context_args = args.split() if args else []
                            self.handle_context(context_args)

                        elif command == "models":
                            self.handle_models()
                        
                        elif command == "qa":
                            if args:
                                self.handle_qa_conversation(args)
                            else:
                                prompt = input("Ask your question: ").strip()
                                if prompt:
                                    self.handle_qa_conversation(prompt)
                            
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
                        # Regular prompt for code generation
                        # Check for @file mentions and add to context
                        files_mentioned = []
                        words = user_input.split()
                        for word in words:
                            if word.startswith("@"):
                                filepath = word[1:]  # Remove @
                                files_mentioned.append(filepath)
                        
                        # Add files to context temporarily for this generation
                        original_context = self.context_files.copy()
                        for filepath in files_mentioned:
                            if filepath not in self.context_files:
                                try:
                                    FileTools.read_file(filepath)  # Verify exists
                                    self.context_files.append(filepath)
                                    self._print_success(f"Added {filepath} to context for this prompt")
                                except ToolsError:
                                    pass
                        
                        # Remove @ mentions from prompt
                        clean_prompt = " ".join([w for w in words if not w.startswith("@")])
                        
                        if clean_prompt.strip():
                            self.handle_generate(clean_prompt, stream=True)
                        
                        # Restore original context
                        self.context_files = original_context

                except KeyboardInterrupt:
                    print()
                    self._print_info("Interrupted by user")
                    continue
                except EOFError:
                    self._print_info("Goodbye!")
                    break
                except Exception as e:
                    self._print_error(f"Unexpected error: {str(e)}")
                    traceback.print_exc()
        except KeyboardInterrupt:
            pass

    def run_single(self, prompt: str) -> None:
        """Run a single generation and exit.
        
        Args:
            prompt: Input prompt
        """
        self.handle_generate(prompt, stream=True)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="DeepX - Code generation CLI using Ollama",
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
        default="http://ollama:11434",
        help="Ollama server URL (default: http://ollama:11434)"
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
        
        cli = DeepXCLI(ollama_url=args.url, model=args.model)

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
