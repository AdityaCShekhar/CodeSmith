# Quick Reference

## Launch

```bash
codesmith                       # Start interactive
codesmith -p "prompt"          # Run single prompt
codesmith --skip-init          # Skip initialization
```

## Commands

```
/write FILE             # Generate code from instructions and save it
/models                 # List models
/help                   # Help
/exit                   # Exit
```

## @ File Context

```
> Write a test for @src/codesmith/cli.py
> Refactor @src/codesmith/cli.py and @src/codesmith/tools.py
Press Tab for autocomplete
```

## Writing Better Prompts

**The Formula:** Specific + Constraints

❌ `> Explain this`  
✅ `> Explain in 3 bullet points: what it does, why, how`

❌ `> Write code`  
✅ `> Write function that validates emails (keep under 10 lines, add type hints)`

## Setup

```bash
echo 'export PATH="/path/to/CodeSmith:$PATH"' >> ~/.zshrc
source ~/.zshrc
codesmith
```

---

Full guides: [USAGE.md](USAGE.md) | [CONTEXT_FEATURE.md](CONTEXT_FEATURE.md) | [PROMPTS.md](PROMPTS.md)
