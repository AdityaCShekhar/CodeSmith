#!/usr/bin/env python3
"""
Demo of DeepX @ context autocomplete feature

This script demonstrates how the @ mention system works in DeepX.
When you type @ in the chat, autocomplete suggestions appear showing
available files you can add to the conversation context.
"""

from pathlib import Path

def demo_file_discovery():
    """Show how DeepX discovers files for @ context."""
    print("=" * 70)
    print("DEMO: DeepX @ Context Autocomplete")
    print("=" * 70)
    print()
    
    # Simulate file discovery
    workspace_dir = Path(".")
    
    files = []
    skip_dirs = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache", 
                 ".docker", ".idea", "dist", "build", ".vscode", ".mypy_cache", ".env"}
    skip_extensions = {".pyc", ".pyo", ".so", ".egg-info"}
    
    def walk_dir(directory, current_depth=0, max_depth=3):
        if current_depth > max_depth:
            return
        try:
            for item in sorted(directory.iterdir()):
                try:
                    if item.name.startswith("."):
                        continue
                    if item.is_dir() and item.name in skip_dirs:
                        continue
                    if item.is_file():
                        if item.suffix in skip_extensions:
                            continue
                        try:
                            rel_path = str(item.relative_to(workspace_dir))
                            files.append(rel_path)
                        except ValueError:
                            pass
                    elif item.is_dir() and current_depth < max_depth:
                        walk_dir(item, current_depth + 1, max_depth)
                except (OSError, PermissionError):
                    continue
        except (OSError, PermissionError):
            pass
    
    walk_dir(workspace_dir)
    files = sorted(set(files))
    
    print("📁 Files discovered for @ context:")
    print("-" * 70)
    for i, f in enumerate(files[:15], 1):
        print(f"  {i:2d}. @{f}")
    
    if len(files) > 15:
        print(f"  ... and {len(files) - 15} more files")
    
    print()
    print("=" * 70)
    print("HOW TO USE @ CONTEXT")
    print("=" * 70)
    print("""
1. TYPE @ in the chat prompt and press Tab to see autocomplete suggestions
   
   Example:
   > Write a test for @
   
   You'll see:
   @llm.py
   @tools.py
   @cli.py
   ...

2. COMPLETE the filename by pressing Tab or typing

   Example:
   > Write a test for @llm.py
   
   The file llm.py will be added to context automatically

3. MENTION MULTIPLE FILES by using @ multiple times

   Example:
   > Create a function using @llm.py @tools.py that combines both

4. CONTEXT IS INJECTED into the prompt sent to the AI

   The file contents are included with your prompt, so the AI
   can see and understand the code in those files.

5. USE /context command for explicit control

   /context              - Show current context files
   /context add file.py  - Add file manually
   /context remove 1     - Remove file by number
   /context clear        - Clear all context

EXAMPLE WORKFLOW:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

> /context add cli.py
✓ Added cli.py to context

> Given the existing CLI structure in @cli.py, write a new command handler for /debug
✓ Added cli.py to context for this prompt

(AI generates the code)

> /context
ℹ Current context files:
  1. cli.py

> Write a test file for this new feature @cli.py

(AI has access to both previous context and can write tests)

---

KEY FEATURES:
✓ Tab autocomplete - see available files as you type @
✓ Fuzzy matching - type @cli to find cli.py files
✓ Persistent context - files stay in context for multiple prompts
✓ Temporary mentions - use @file in a single prompt without persistent context
✓ Works from any directory - file discovery is relative to where you run deepx
""")

if __name__ == "__main__":
    demo_file_discovery()
