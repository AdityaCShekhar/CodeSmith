#!/usr/bin/env python3
"""Demonstrate CodeSmith's current generation and file workflow."""

from pathlib import Path

from cli import DeepXCLI
from tools import FileTools


def demo() -> None:
    """Generate code, save it, and use it as temporary prompt context."""
    print("=" * 70)
    print("CodeSmith - Code Generation Demo")
    print("=" * 70)

    cli = DeepXCLI()

    print("\n[1] Generate code")
    prompt = """Write a Python function called factorial that:
- accepts a non-negative integer
- raises ValueError for negative input
- includes type hints
- contains only the code, with minimal comments"""
    generated = cli.handle_generate(prompt, stream=True)

    print("\n[2] Save generated code")
    output_file = Path("example_factorial.py")
    FileTools.write_file(str(output_file), generated.strip())
    print(f"Saved generated code to {output_file}")

    print("\n[3] Generate code using file context")
    print("In the interactive CLI, the equivalent workflow is:")
    print(f"  ➜ Explain @{output_file}")
    print(f"  ➜ Write tests for @{output_file}")

    print("\nDemo complete.")


if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        print("\nDemo interrupted")

