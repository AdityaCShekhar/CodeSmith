#!/usr/bin/env python3
"""
Example usage script for DeepX CLI with proper prompts.
Shows how to write clear, specific prompts for readable responses.

See PROMPT_ENGINEERING.md for prompt writing best practices.
"""

from cli import DeepXCLI
from tools import FileTools, ShellTools

def demo():
    """Run demonstration of DeepX features with good prompts."""
    print("=" * 70)
    print("DeepX - Code Generation CLI Demo (with better prompts)")
    print("=" * 70)
    print()
    print("💡 Tip: See PROMPT_ENGINEERING.md for how to write clear prompts")
    print()

    # Initialize the CLI
    cli = DeepXCLI(
        ollama_url="http://ollama:11434",
        model="deepseek-coder:1.3b"
    )

    # Demo 1: Simple code generation with SPECIFIC prompt
    print("\n" + "=" * 70)
    print("[Demo 1] Simple Code Generation (Specific Prompt)")
    print("=" * 70)
    print("Prompt: Write a Python function to calculate factorial.")
    print("        Include error handling for negative numbers.")
    print("        Keep it under 10 lines.")
    print("-" * 70)
    prompt = """Write a Python function called factorial that:
- Takes an integer n as input
- Returns n! (factorial of n)
- Raises ValueError if n is negative
- Keep it under 10 lines
- Include type hints"""
    cli.handle_generate(prompt, stream=True)

    # Demo 2: Write to file
    print("\n" + "=" * 70)
    print("[Demo 2] Writing Code to File")
    print("=" * 70)
    code = '''def factorial(n: int) -> int:
    """Calculate n! (factorial of n).
    
    Args:
        n: A non-negative integer
        
    Returns:
        The factorial of n
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return 1
    return n * factorial(n - 1)


if __name__ == "__main__":
    # Test factorial function
    for i in range(6):
        print(f"{i}! = {factorial(i)}")
'''
    try:
        msg = FileTools.write_file("example_factorial.py", code)
        print(f"✓ {msg}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Demo 3: Read file
    print("\n" + "=" * 70)
    print("[Demo 3] Reading File Content")
    print("=" * 70)
    try:
        content = FileTools.read_file("example_factorial.py")
        print(content)
    except Exception as e:
        print(f"✗ Error: {e}")

    # Demo 4: Generate tests with SPECIFIC prompt
    print("\n" + "=" * 70)
    print("[Demo 4] Generate Unit Tests (Specific Prompt)")
    print("=" * 70)
    print("Prompt: Write 3 unit tests covering normal, edge, and error cases")
    print("-" * 70)
    prompt = """Write 3 unit test cases for the factorial function in example_factorial.py:
1. Test case 1: Test factorial(5) returns 120
2. Test case 2: Test factorial(0) returns 1 (edge case)
3. Test case 3: Test factorial(-1) raises ValueError (error case)

Use Python's unittest framework. Keep it concise."""
    cli.handle_generate(prompt, stream=True)

    # Demo 5: Run shell command
    print("\n" + "=" * 70)
    print("[Demo 5] Running Shell Command")
    print("=" * 70)
    print("Running: python3 example_factorial.py")
    print("-" * 70)
    try:
        output = ShellTools.safe_command("python3 example_factorial.py")
        print(output)
    except Exception as e:
        print(f"✗ Error: {e}")

    # Demo 6: Context-based code generation
    print("\n" + "=" * 70)
    print("[Demo 6] Using File Context for Better Responses")
    print("=" * 70)
    print("Adding example_factorial.py to context...")
    print("Prompt: Write optimized version using iterative approach")
    print("-" * 70)
    cli.handle_context(["add", "example_factorial.py"])
    prompt = """Looking at the factorial function in the context:
- Rewrite it using iteration instead of recursion
- Keep the same function signature and error handling
- Add performance comparison as a comment
- Use only 8-12 lines"""
    cli.handle_generate(prompt, stream=True)

    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print("\n📚 Next steps:")
    print("1. Read PROMPT_ENGINEERING.md for prompt writing tips")
    print("2. Try: deepx -p \"Your specific prompt here\"")
    print("3. Use /context to add files for better responses")
    print()

if __name__ == "__main__":
    try:
        demo()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()
