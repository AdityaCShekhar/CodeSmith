#!/bin/bash
# Quick Start Guide for CodeSmith

cat << 'EOF'

╔════════════════════════════════════════════════════════════════════╗
║                    CodeSmith - Code Generation CLI                    ║
║                    Quick Start Guide                               ║
╚════════════════════════════════════════════════════════════════════╝

📋 TABLE OF CONTENTS
═══════════════════════════════════════════════════════════════════════
1. Project Overview
2. What's Included
3. Quick Setup (Docker Compose)
4. Running the CLI
5. First Code Generation
6. Common Use Cases
7. Troubleshooting

═══════════════════════════════════════════════════════════════════════
1️⃣  PROJECT OVERVIEW
═══════════════════════════════════════════════════════════════════════

CodeSmith is a powerful CLI tool similar to OpenAI Codex that runs locally
using Ollama. It allows you to:

  ✨ Generate code from natural language prompts
  📝 Read and write files directly from the CLI
  🧠 Inject file context for smarter generation
  📊 Stream responses for real-time feedback

═══════════════════════════════════════════════════════════════════════
2️⃣  WHAT'S INCLUDED
═══════════════════════════════════════════════════════════════════════

Core Modules:
  └─ cli.py          → Main CLI application with REPL loop
  └─ llm.py          → Ollama API client with streaming support
  └─ tools.py        → File operations and shell utilities

Configuration:
  └─ requirements.txt → Python dependencies
  └─ docker-compose.yml → Container setup
  └─ Dockerfile       → Docker image definition

Documentation:
  └─ README.md        → Complete documentation
  └─ ARCHITECTURE.md  → Design and implementation details
  └─ setup.sh         → Automated setup script

Examples:
  └─ demo.py          → Usage demonstration script

═══════════════════════════════════════════════════════════════════════
3️⃣  QUICK SETUP (DOCKER COMPOSE - RECOMMENDED)
═══════════════════════════════════════════════════════════════════════

Prerequisites:
  • Docker and Docker Compose installed
  • ~10GB disk space for model
  • 2GB RAM minimum (more recommended)

Setup Steps:

1. Clone/navigate to project:
   $ cd /Users/aditya/Projects/DeepX

2. Start services:
   $ docker-compose up -d ollama

3. Start the CLI (auto-pulls model on first run):
   $ codesmith
   
   ⏳ First time: waits for Ollama, pulls model (2-5 minutes)
   ✓ Next times: instant startup

4. Monitor progress (if needed):
   $ docker-compose logs -f ollama

═══════════════════════════════════════════════════════════════════════
4️⃣  RUNNING THE CLI
═══════════════════════════════════════════════════════════════════════

After setup, simply type:
  $ codesmith

The model is automatically pulled and checked on startup.

Other options:

Option A: Using codesmith command (fast)
  $ codesmith
  $ codesmith -p "Write hello world"

Option B: Using Docker Compose
  $ docker-compose run --rm deepx-cli

Option C: Local Python (requires Ollama running separately)
  $ pip install -r requirements.txt
  $ python3 cli.py

Option D: Custom Ollama URL
  $ codesmith --url http://localhost:11434 --model deepseek-coder:1.3b

═══════════════════════════════════════════════════════════════════════
5️⃣  FIRST CODE GENERATION
═══════════════════════════════════════════════════════════════════════

After starting the CLI, you'll see:

  ━━ CodeSmith - Code Generation CLI ━━
  ℹ Connected to Ollama at http://ollama:11434
  ℹ Using model: deepseek-coder:1.3b
  ℹ Type /help for available commands

  >

Type a prompt and press Enter:

  > Write a Python function to calculate fibonacci numbers

The AI will generate code in real-time:

  ━━ Generating ━━
  ℹ Temperature: 0.7 | Top-p: 0.9

  ```python
  def fibonacci(n):
      if n <= 0:
          return []
      elif n == 1:
          return [0]
      
      fib_sequence = [0, 1]
      for i in range(2, n):
          fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
      
      return fib_sequence[:n]

  if __name__ == "__main__":
      print(fibonacci(10))
  ```

  >

═══════════════════════════════════════════════════════════════════════
6️⃣  COMMON USE CASES
═══════════════════════════════════════════════════════════════════════

USE CASE 1: Generate and Save Code
─────────────────────────────────────
  > Write a Python function to parse JSON files
  # Output appears
  /write json_parser.py
  ✓ Successfully wrote 1245 bytes to json_parser.py

USE CASE 2: Code with Context
─────────────────────────────────────
  @utils.py
  @config.json
  > Generate tests for the functions in utils.py following the patterns
  # AI generates informed by the context files

USE CASE 3: Read and Understand Code
─────────────────────────────────────
  > Explain what this code does and suggest improvements

USE CASE 4: Execute and Test
─────────────────────────────────────
  /write test_script.py
  # [paste your generated code]

USE CASE 5: Iterative Development
──────────────────────────────────
  > Generate a web scraper for hackernews.com
  /write scraper.py
  ✗ Error: requests module not found
  > Generate the same scraper but using built-in libraries
  /write scraper_builtin.py

═══════════════════════════════════════════════════════════════════════
AVAILABLE COMMANDS
═══════════════════════════════════════════════════════════════════════

Generation:
  > Your prompt here     Generate code from a prompt

File Operations:
  /write <file>        Generate code from instructions and save it

Context Management:
  @<file>  Add file to context for smarter generation

Utilities:
  /models              List available models
  /help                Show all commands
  /exit                Exit the CLI

═══════════════════════════════════════════════════════════════════════
7️⃣  TROUBLESHOOTING
═══════════════════════════════════════════════════════════════════════

Problem: "Cannot connect to Ollama at http://ollama:11434"
Solution: 
  • Make sure Ollama is running: docker-compose ps
  • Check logs: docker-compose logs ollama
  • Verify with: curl http://localhost:11434/api/tags (if local)
  • Start Ollama: docker-compose up -d ollama

Problem: "Model deepseek-coder:1.3b not found"
Solution:
  • Pull the model: docker-compose exec ollama ollama pull deepseek-coder:1.3b
  • Check available: /models

Problem: Slow responses
Solution:
  • Reduce context files for shorter prompts
  • Use lighter model or smaller hardware is available
  • Ensure Ollama has enough CPU/memory

Problem: File not found when reading
Solution:
  • Use absolute or relative paths from working directory

Problem: "Exit code: 127" when running command
Solution:
  • Command not found in container
  • Install dependencies within the container

═══════════════════════════════════════════════════════════════════════
USEFUL DOCKER COMMANDS
═══════════════════════════════════════════════════════════════════════

View running containers:
  $ docker-compose ps

View logs:
  $ docker-compose logs -f ollama    # Ollama logs
  $ docker-compose logs -f            # All logs

Stop services:
  $ docker-compose down

Stop and remove volumes:
  $ docker-compose down -v

Restart Ollama:
  $ docker-compose restart ollama

Access Ollama shell directly:
  $ docker-compose exec ollama bash

═══════════════════════════════════════════════════════════════════════
ADVANCED USAGE
═══════════════════════════════════════════════════════════════════════

1. Using Different Models

   Check available models:
   /models

   Use different model (if installed):
   python3 cli.py --model codellama:latest

   Pull new model to Ollama:
   docker-compose exec ollama ollama pull your-model-name

2. Disable Streaming (slower start, full response at once)
   python3 cli.py --no-stream

3. Run in background:
   docker-compose run -d deepx-cli
   # Then interact via docker-compose exec

4. Mount a workspace directory for easier file access:
   docker-compose run --rm -v $(pwd):/workspace deepx-cli

═══════════════════════════════════════════════════════════════════════
PERFORMANCE TIPS
═══════════════════════════════════════════════════════════════════════

1. Keep context files minimal (only relevant files)
2. Use short, clear prompts for faster inference
3. Increase Docker memory for faster generation
4. Run Ollama on GPU if available (modify docker-compose.yml)
5. Batch similar requests to warm up the model

═══════════════════════════════════════════════════════════════════════
NEXT STEPS
═══════════════════════════════════════════════════════════════════════

1. Run the CLI: docker-compose run --rm deepx-cli
2. Type /help to see all commands
3. Generate your first code: "Write a hello world program"
5. Read README.md for complete documentation
6. Check ARCHITECTURE.md for technical details
7. Try the demo script: python3 demo.py

═══════════════════════════════════════════════════════════════════════
CLEANUP
═══════════════════════════════════════════════════════════════════════

To stop and remove everything:
  $ docker-compose down -v

To remove just the containers but keep data:
  $ docker-compose down

To remove images too:
  $ docker-compose down --rmi all

═══════════════════════════════════════════════════════════════════════

For detailed documentation, see:
  • README.md - Complete feature documentation
  • ARCHITECTURE.md - Design and implementation details

Happy coding! 🚀

EOF
