# CodeSmith - Setup & Usage

## Quick Start — macOS and Linux

```bash
# 1. Add to PATH (one-time)
echo 'export PATH="/path/to/CodeSmith:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 2. Run from anywhere
codesmith
```

## Quick Start — Windows

Add the CodeSmith repository directory to your User `PATH`, restart Windows
Terminal, and run `codesmith`. The `codesmith.cmd` launcher preserves the
current repository as your workspace.

## Run Options

```bash
codesmith                              # Interactive mode
codesmith -p "your prompt"            # Single prompt
codesmith --url http://localhost:11434 # Custom Ollama URL
codesmith --skip-init                 # Skip initialization
```

## Chat Commands

- `/write file.py` - Generate code from instructions and save it
- `/models` - List available models
- `/help` - Show help
- `/exit` - Quit

## @ File Context

Add files to your prompt with `@`:

```
> Write a test for @src/codesmith/cli.py
✓ Added src/codesmith/cli.py to context

> Refactor based on patterns in @src/codesmith/cli.py and @src/codesmith/tools.py
```

Type `@` to see autocomplete suggestions immediately. Press **Tab** to select.

## Getting Good Responses

**Key:** Write specific prompts, not vague ones.

❌ Bad: `> Explain this file`  
✅ Good: `> What does this file do in 3 bullet points?`

See **PROMPTS.md** for complete guide on writing clear prompts.

## Features

✅ Works from any directory  
✅ No `init.py` dependency  
✅ Tab autocomplete for files  
✅ Multiple file context support  
✅ Temporary file context with `@filename`
✅ Auto-initialization  
✅ Docker Compose compatible  

---

See [CONTEXT_FEATURE.md](CONTEXT_FEATURE.md) for detailed @ feature guide.  
See [PROMPTS.md](PROMPTS.md) for how to write effective prompts.
