# Quick Reference

## Launch

```bash
deepx                       # Start interactive
deepx -p "prompt"          # Run single prompt
deepx --skip-init          # Skip initialization
```

## Commands

```
/read FILE              # Read file
/write FILE             # Save code
/run CMD                # Run command
/context add FILE       # Add to context
/context remove N       # Remove from context
/context                # Show context
/models                 # List models
/help                   # Help
/exit                   # Exit
```

## @ File Context

```
> Write a test for @cli.py
> Refactor @cli.py and @tools.py
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
echo 'export PATH="/Users/aditya/Projects/DeepX:$PATH"' >> ~/.zshrc
source ~/.zshrc
deepx
```

---

Full guides: [USAGE.md](USAGE.md) | [CONTEXT_FEATURE.md](CONTEXT_FEATURE.md) | [PROMPTS.md](PROMPTS.md)
