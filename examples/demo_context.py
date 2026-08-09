#!/usr/bin/env python3
"""Demonstrate CodeSmith's temporary @filename context workflow."""

from pathlib import Path
from typing import List


SKIP_DIRS = {
    ".git", "__pycache__", ".venv", "node_modules", ".pytest_cache",
    ".docker", ".idea", "dist", "build", ".vscode", ".mypy_cache", ".env",
}
SKIP_EXTENSIONS = {".pyc", ".pyo", ".so", ".egg-info"}


def discover_files(workspace: Path, max_depth: int = 3) -> List[str]:
    """Return files available for @ autocomplete."""
    files: List[str] = []

    def walk(directory: Path, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            entries = sorted(directory.iterdir())
        except (OSError, PermissionError):
            return

        for item in entries:
            if item.name.startswith(".") or item.name in SKIP_DIRS:
                continue
            if item.is_file() and item.suffix not in SKIP_EXTENSIONS:
                files.append(str(item.relative_to(workspace)))
            elif item.is_dir():
                walk(item, depth + 1)

    walk(workspace, 0)
    return sorted(set(files))


def demo_file_discovery() -> None:
    """Show how files become available for @ suggestions."""
    workspace = Path.cwd()
    files = discover_files(workspace)

    print("=" * 70)
    print("CodeSmith - @ File Context Demo")
    print("=" * 70)
    print(f"\nWorkspace: {workspace}")
    print("\nFiles available for autocomplete:")
    for filepath in files[:20]:
        print(f"  @{filepath}")

    if len(files) > 20:
        print(f"  ... and {len(files) - 20} more")

    print("""
How to use temporary file context:

  1. Type @ in CodeSmith to open file suggestions.
  2. Type part of a filename, such as @cli, to filter the list.
  3. Select a file and include it in your prompt:

      ➜ Explain @src/codesmith/cli.py
      ➜ Write tests for @src/codesmith/tools.py
      ➜ Compare @src/codesmith/llm.py with @src/codesmith/tools.py

The mentioned files are included for that prompt only. Mention them again
when they are needed in a later prompt.
""")


if __name__ == "__main__":
    demo_file_discovery()
