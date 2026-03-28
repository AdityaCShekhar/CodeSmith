#!/usr/bin/env python3
"""CLI tool similar to OpenAI Codex using local Ollama."""

import sys
import argparse
import traceback
from typing import Optional
from pathlib import Path

from llm import OllamaClient, OllamaError
from tools import FileTools, ShellTools, ContextInjector, ToolsError

# ANSI color codes
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_CYAN = "\033[36m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"
COLOR_GRAY = "\033[90m"


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

    def _print_info(self, message: str) -> None:
        """Print info message."""
        print(f"{COLOR_CYAN}ℹ {message}{COLOR_RESET}")

    def _print_success(self, message: str) -> None:
        """Print success message."""
        print(f"{COLOR_GREEN}✓ {message}{COLOR_RESET}")

    def _print_error(self, message: str) -> None:
        """Print error message."""
        print(f"{COLOR_RED}✗ {message}{COLOR_RESET}")

    def _print_header(self, title: str) -> None:
        """Print formatted header."""
        print(f"\n{COLOR_BOLD}{COLOR_CYAN}━━ {title} ━━{COLOR_RESET}")

    def _format_code_block(self, code: str, language: str = "python") -> str:
        """Format code for display."""
        return f"{COLOR_GRAY}```{language}\n{COLOR_RESET}{code}{COLOR_GRAY}\n```{COLOR_RESET}"

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

        try:
            if stream:
                result = ""
                for token in self.client.generate(prompt, stream=True):
                    result += token
                    print(token, end="", flush=True)
                print()  # Newline after streaming
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
        print(f"{COLOR_BOLD}Enter content (Ctrl+D to save):{COLOR_RESET}")
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

    def print_help(self) -> None:
        """Print help message."""
        help_text = f"""
{COLOR_BOLD}DeepX - Code Generation CLI{COLOR_RESET}

{COLOR_BOLD}Commands:{COLOR_RESET}
  /write <filename>     Write input to file
  /read <filename>      Read and display file
  /run <command>        Execute shell command
  /context add <file>   Add file to context
  /context remove <n>   Remove context file by number
  /context              Show current context
  /models              List available models
  /help                Show this help
  /exit                Exit the application

{COLOR_BOLD}Usage:{COLOR_RESET}
  Simply type your code generation prompts and press Enter.
  The AI will generate code based on your request.
  
{COLOR_BOLD}Example:{COLOR_RESET}
  > Write a Python function to calculate factorial
  > /context add utils.py
  > /read utils.py
  > /write output.py

"""
        print(help_text)

    def repl(self) -> None:
        """Run interactive REPL loop."""
        self._print_header("DeepX - Code Generation CLI")
        self._print_info("Type /help for available commands")
        print()

        while True:
            try:
                user_input = input(f"{COLOR_BOLD}> {COLOR_RESET}").strip()

                if not user_input:
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

                    else:
                        self._print_error(f"Unknown command: /{command}")

                else:
                    # Regular prompt for code generation
                    self.handle_generate(user_input, stream=True)

            except KeyboardInterrupt:
                print()
                self._print_info("Interrupted by user")
                continue
            except Exception as e:
                self._print_error(f"Unexpected error: {str(e)}")
                traceback.print_exc()

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

    args = parser.parse_args()

    try:
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
