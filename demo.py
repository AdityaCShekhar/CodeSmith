#!/usr/bin/env python3
"""
Example usage script for DeepX CLI.
This demonstrates the main features.
"""

from cli import CodexCLI
from tools import FileTools, ShellTools

def demo():
    """Run demonstration of DeepX features."""
    print("=" * 60)
    print("DeepX - Code Generation CLI Demo")
    print("=" * 60)
    print()

    # Initialize the CLI
    cli = DeepXCLI(
        ollama_url="http://ollama:11434",
        model="deepseek-coder:1.3b"
    )

    # Demo 1: Simple code generation
    print("\n[Demo 1] Simple Code Generation")
    print("-" * 60)
    prompt = "Write a Python function to calculate the factorial of a number"
    cli.handle_generate(prompt, stream=True)

    # Demo 2: Write to file
    print("\n[Demo 2] Writing Code to File")
    print("-" * 60)
    code = '''def factorial(n):
    """Calculate factorial of n."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)

if __name__ == "__main__":
    for i in range(6):
        print(f"{i}! = {factorial(i)}")
'''
    try:
        msg = FileTools.write_file("example.py", code)
        print(f"✓ {msg}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Demo 3: Read file
    print("\n[Demo 3] Reading File Content")
    print("-" * 60)
    try:
        content = FileTools.read_file("example.py")
        print(content[:200] + "..." if len(content) > 200 else content)
    except Exception as e:
        print(f"✗ Error: {e}")

    # Demo 4: Run shell command
    print("\n[Demo 4] Running Shell Command")
    print("-" * 60)
    try:
        output = ShellTools.safe_command("python3 example.py")
        print(output)
    except Exception as e:
        print(f"✗ Error: {e}")

    # Demo 5: Context injection
    print("\n[Demo 5] Context Injection")
    print("-" * 60)
    cli.handle_context(["add", "example.py"])
    prompt = "Based on the example file, generate a test suite"
    cli.handle_generate(prompt, stream=True)

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()
