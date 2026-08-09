# CodeSmith - Setup & Usage

## Quick Start

```bash
# 1. Add to PATH (one-time)
echo 'export PATH="/Users/aditya/Projects/DeepX:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 2. Run from anywhere
codesmith
```

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
> Write a test for @cli.py
✓ Added cli.py to context

> Refactor based on patterns in @cli.py and @tools.py
```

Press **Tab** after `@` to see autocomplete suggestions.

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
