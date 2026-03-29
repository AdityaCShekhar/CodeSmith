# DeepX @ Context Feature Guide

## Overview

The `@` symbol in DeepX allows you to easily add file context to your code generation prompts. When you mention a file with `@filename`, its contents are automatically included in the prompt sent to the AI model.

## Quick Start

### 1. Type a prompt with @ mention

```
> Write a test for @cli.py
```

### 2. Press Tab for autocomplete

Start typing `@` and files will appear:
```
@cli.py
@llm.py
@tools.py
@ARCHITECTURE.md
```

### 3. AI generates code with file context

The model sees the contents of `cli.py` and can write tests based on its actual implementation.

## Features

### ✨ Tab Autocomplete

**How it works:**
- Type `@` anywhere in your prompt
- Press Tab to see available files
- Use arrow keys to navigate
- Press Enter to select

**Example:**
```
> Generate a handler based on existing patterns in @
<Tab shows file suggestions>
```

### 🔍 Fuzzy Matching

Search for files by typing part of the name:

```
> Fix the bug in @too
<Shows only files containing "too">
@tools.py    Add to context
```

### 📁 Multiple File Context

Include multiple files by using `@` multiple times:

```
> Create integration between @cli.py and @llm.py

✓ Added cli.py to context for this prompt
✓ Added llm.py to context for this prompt
```

### 📌 Persistent vs Temporary Context

**Temporary (for current prompt only):**
```
> Write a test for @cli.py
(File context is used for this prompt only)
```

**Persistent (for multiple prompts):**
```
> /context add cli.py
✓ Added cli.py to context

> Now add error handling to the generate function
(cli.py is still in context)

> Also write a test for the error handling
(cli.py remains in context)
```

### 🎮 Commands for Context Management

```
/context                  # Show current context files
/context add file.py      # Manually add a file
/context remove 1         # Remove file by index
/context clear            # Clear all context files
```

## Usage Examples

### Example 1: Write a test for existing code

```
> Write unit tests for the OllamaClient class in @llm.py

✓ Added llm.py to context for this prompt

<AI reviews llm.py and generates tests>
```

### Example 2: Create feature based on patterns

```
> Looking at the structure in @cli.py, create a new handler for /analyze command

✓ Added cli.py to context for this prompt

<AI reviews the CLI structure and implements similar patterns>
```

### Example 3: Multi-file integration

```
> Create a new ShellTools method in @tools.py that integrates with the error handling in @llm.py

✓ Added tools.py to context for this prompt  
✓ Added llm.py to context for this prompt

<AI creates code that fits both files' patterns>
```

### Example 4: Documentation based on code

```
> Update the section in @README.md for the OllamaClient based on @llm.py

✓ Added README.md to context for this prompt
✓ Added llm.py to context for this prompt

<AI updates documentation to match actual implementation>
```

## Technical Details

### File Discovery

DeepX automatically discovers files from:
- Current directory (`.`)
- Docker container mount (`/work`)
- Workspace directory (`/workspace`)

**Skipped:**
- Hidden files (starting with `.`)
- Cache directories (`__pycache__`, `.pytest_cache`, etc.)
- Binary files (`.pyc`, `.so`, etc.)
- Large folder structures (max depth: 3)

### How It Works

1. **Autocomplete Phase**
   - User types `@` in any position
   - Completer finds the last `@` symbol
   - Displays matching files

2. **Context Injection Phase**
   - User sends prompt with `@filename` mentions
   - DeepX extracts file paths
   - File contents are prepended to prompt
   - Sent to LLM with full context

3. **Cleanup Phase**
   - `@` symbols are removed from prompt
   - AI receives clean, context-aware prompt
   - File contents are included separately

## Tips & Tricks

### 🎯 Precise Questions

With context, ask more specific questions:

```
// Good
> Write a test for the read_file method in @tools.py

// Not as good (without context)
> Write a test for reading files
```

### 📚 Build on Existing Code

Reference multiple files to understand patterns:

```
> Looking at how commands are handled in @cli.py and 
  the tool patterns in @tools.py, implement a new 
  handler called /validate

✓ Added cli.py to context for this prompt
✓ Added tools.py to context for this prompt
```

### 🔄 Iterative Development

Use persistent context for back-and-forth development:

```
> /context add cli.py
> Add a new command handler

> Now add error handling to it
> (cli.py is still in context)

> Write tests for this handler
> (cli.py is still in context)
```

### 💾 Save Generated Code

After generation, save directly:

```
> Write a test class for @cli.py

(AI generates test code)

> /write test_cli.py

Enter content (Ctrl+D to save):
<paste generated code>
```

## Common Workflows

### Refactoring

```
> Refactor the OllamaClient initialization in @llm.py to use a connection pool

The AI sees the current implementation and suggests improvements
```

### Feature Addition

```
> Add a streaming option to the handle_generate method in @cli.py, 
  based on the existing streaming pattern in @llm.py

The AI has both files' context and can implement consistently
```

### Documentation

```
> Update the docstrings in @cli.py to match the documentation in @README.md

AI can keep docs and code in sync
```

### Bug Fixing

```
> There's a bug when the context is empty. Fix it in @cli.py

AI sees the actual code and can spot the issue
```

## Troubleshooting

### Files not showing in autocomplete?

Make sure:
- Files are in the current directory or subdirectories (max 3 levels deep)
- Files aren't in ignored directories (`.git`, `__pycache__`, etc.)
- Files have non-binary extensions

Test with:
```
> /debug-files
```

### @ mention not being recognized?

- Ensure there's a space before `@`: `> text @file.py` ✓
- Don't use `@ filename` (space between @ and name)
- Use complete or partial filename: `@cli.py` or `@cli`

### Changes not reflected in generated code?

- File contents are read at prompt time
- Save your changes to disk first
- If file is in persistent context, it's read fresh each time

---

**Now you can leverage file context to get better, more accurate code generation!** 🚀

