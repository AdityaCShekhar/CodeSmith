# DeepX - Setup & Usage

## Quick Start

```bash
# 1. Add to PATH (one-time)
echo 'export PATH="/Users/aditya/Projects/DeepX:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 2. Run from anywhere
deepx
```

## Run Options

```bash
deepx                              # Interactive mode
deepx -p "your prompt"            # Single prompt
deepx --url http://localhost:11434 # Custom Ollama URL
deepx --skip-init                 # Skip initialization
```

## Chat Commands

- `/read file.py` - View file
- `/write file.py` - Save code
- `/run command` - Execute shell command
- `/context add file` - Add to persistent context
- `/context remove N` - Remove by index
- `/context` - Show current context
- `/models` - List available models
- `/help` - Show help
- `/exit` - Quit

## @ File Context

Add files to your prompt with `@`:

```
> Write a test for @cli.py
✓ Added cli.py to context

> /context add tools.py
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
✅ Persistent context manager  
✅ Auto-initialization  
✅ Docker Compose compatible  

---

See [CONTEXT_FEATURE.md](CONTEXT_FEATURE.md) for detailed @ feature guide.  
See [PROMPTS.md](PROMPTS.md) for how to write effective prompts.
