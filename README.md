# CodeSmith - Code Generation CLI

A powerful CLI tool for code generation using a local Ollama instance. Think of it as your personal OpenAI Codex alternative running on your machine. Built with Python, this tool provides an interactive REPL for generating code, reading, and writing files.

## Features

- 🚀 **Code Generation**: Generate code from natural language prompts
- 📝 **File Operations**: Read, write, and manage files seamlessly
- 🧠 **Context Injection**: Include file contents in prompts for context-aware generation
- 📊 **Streaming Support**: Real-time token streaming from Ollama
- 🎯 **Multiple Models**: Support for any Ollama-hosted model
- 🎨 **Clean Output**: Formatted responses with color-coded sections
- 🐳 **Docker Ready**: Easy deployment with Docker and Docker Compose

## Architecture

```
CodeSmith/
├── src/codesmith/          # Installable Python package
│   ├── cli.py              # Interactive CLI and command handling
│   ├── llm.py              # Ollama API client
│   ├── tools.py            # File and context utilities
│   └── batch.py            # Batch-generation entry point
├── examples/               # Runnable examples and sample input
├── docs/                   # Project documentation
├── scripts/                # Setup and maintenance helpers
├── codesmith               # macOS/Linux launcher
├── codesmith.cmd           # Windows launcher
├── pyproject.toml          # Package metadata and entry points
├── Dockerfile
└── docker-compose.yml
```

### Components

- **src/codesmith/cli.py**: Interactive REPL with color-coded output and command handling
- **src/codesmith/llm.py**: Ollama API client with streaming support and error handling
- **src/codesmith/tools.py**: File I/O and context injection utilities
- **src/codesmith/batch.py**: Non-interactive batch generation
- **pyproject.toml**: Package metadata, dependencies, and CLI entry points

## Requirements

- Python 3.8+
- Docker & Docker Compose (for containerized setup)
- OR Ollama running locally at `http://localhost:11434`

## Quick Command Setup

To use `codesmith` from anywhere on macOS or Linux:

```bash
# Option 1: Add to PATH (recommended)
export PATH="/path/to/CodeSmith:$PATH"

# Add to ~/.zshrc or ~/.bashrc to make permanent:
echo 'export PATH="/path/to/CodeSmith:$PATH"' >> ~/.zshrc

# Or symlink to /usr/local/bin
sudo ln -sf /path/to/CodeSmith/codesmith /usr/local/bin/codesmith
```

Then simply type:
```bash
codesmith                    # Interactive mode
codesmith -p "Your prompt"   # Single command
```

On Windows, add the CodeSmith repository directory to your User `PATH` in
Settings, restart Windows Terminal, and run:

```powershell
codesmith
codesmith -p "Your prompt"
```

Windows automatically uses `codesmith.cmd`; macOS and Linux use `codesmith`.

## Installation & Setup

### Option 1: Docker Compose (Recommended)

The easiest way to run everything together:

```bash
# Clone/navigate to the project
cd /path/to/CodeSmith

# Start Ollama (model auto-pulls when CLI starts)
docker compose up -d

# Run the CLI
codesmith

# Stop everything
docker compose down
```

### Option 2: Local Installation

1. **Ensure Ollama is running:**
   ```bash
   # Install Ollama from https://ollama.ai
   # Then start the server
   ollama serve
   ```

2. **In another terminal, pull the model:**
   ```bash
   ollama pull deepseek-coder:1.3b
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the CLI:**
   ```bash
   codesmith
   ```

## Usage

### Interactive REPL Mode

```bash
codesmith
```

Or:
```bash
codesmith
```

### Single Prompt Mode

```bash
codesmith -p "Write a Python function to calculate fibonacci"
```

Or:
```bash
codesmith -p "Write a Python function to calculate fibonacci"
```

### Custom Ollama URL and Model

```bash
codesmith --url http://localhost:11434 --model deepseek-coder:1.3b
```

Or:
```bash
codesmith --url http://localhost:11434 --model deepseek-coder:1.3b
```

## Commands

All commands start with `/`. Here are the available commands:

### Code Generation
Simply type your prompt without a `/` prefix:
```
> Write a Python function to reverse a string
```

### File Generation

**Generate and write a file:**
```
/write <filename>
```
Then enter instructions for the code you want generated and saved.

### File Context

Mention files directly in a prompt. Their contents are included for that
prompt only:
```
> Explain @filename.py and suggest improvements
> Write tests for @utils.py and @models.py
```

### Utilities

**List available models:**
```
/models
```

**Show help:**
```
/help
```

**Exit:**
```
/exit
```

## Usage Examples

### Example 1: Generate a Python Function

```
> Write a Python function to count vowels in a string

⭐ Generating
ℹ Temperature: 0.7 | Top-p: 0.9

```python
def count_vowels(s):
    vowels = 'aeiouAEIOU'
    return sum(1 for c in s if c in vowels)

result = count_vowels('Hello World')
print(result)  # Output: 3
```
```

### Example 2: Generate Code with Context

```
@style.py

> Generate a class that follows the patterns in the context file

⭐ Generating
ℹ Temperature: 0.7 | Top-p: 0.9

[generates code following the style patterns]
```

### Example 3: Write Generated Code to File

```
> Write a function to parse CSV files

[AI generates code]

/write csv_parser.py

✓ Successfully wrote 1245 bytes to csv_parser.py
```

### Example 4: Test the Generated Code

```

⭐ Running: python csv_parser.py --test
STDOUT:
All tests passed!
```

## Command-Line Options

```bash
codesmith --help

options:
  -h, --help            show this help message and exit
  -u URL, --url URL     Ollama server URL (default: http://localhost:11434)
  -m MODEL, --model MODEL
                        Model name (default: deepseek-coder:1.3b)
  -p PROMPT, --prompt PROMPT
                        Single prompt to execute and exit
  --no-stream           Disable streaming mode
```

## Automation

Generate and save code automatically without interactive mode!

### Quick Automation Examples

```bash
# Single file generation
codesmith-batch quicksort.py "Write a quicksort implementation"

# Batch generation from JSON config
codesmith-batch batch.json

# Generates and saves files automatically!
```

### Batch Generation

Create a `batch.json` file:

```json
{
  "tasks": [
    {
      "output": "quicksort.py",
      "prompt": "Write a quicksort algorithm with tests"
    },
    {
      "output": "api.py",
      "prompt": "Create a Flask REST API with CRUD endpoints"
    },
    {
      "output": "tests.py",
      "prompt": "Write comprehensive unit tests"
    }
  ]
}
```

Then run:
```bash
codesmith-batch batch.json
```

All files are generated and saved automatically!

### Usage

```bash
# Single file
codesmith-batch <output_file> "<prompt>"

# Batch from JSON
codesmith-batch <config.json>

# With custom model
codesmith-batch <output_file> "<prompt>" --model mistral:latest
```

**See [AUTOMATION.md](docs/AUTOMATION.md) for complete automation guide**

## Docker Usage

### Using Docker Compose (Complete Setup)

```bash
# Start both Ollama and CLI services
docker compose up -d ollama

# Start the CLI (automatically pulls model on first run)
docker compose run --rm codesmith-cli

# Or use the codesmith command shortcut
codesmith

# View Ollama logs
docker compose logs ollama

# Stop everything
docker compose down -v
```

### Using Docker with Local Ollama

```bash
# Build the image
docker build -t codesmith-cli .

# Run the container (connect to local Ollama)
docker run -it --rm \
  -e OLLAMA_URL=http://host.docker.internal:11434 \
  -v $(pwd)/workspace:/workspace \
  codesmith-cli
```

## Features in Detail

### Streaming Support

The CLI streams responses token-by-token as they're generated, providing real-time feedback:

```
> Write a hello world program in Rust
```python
fn main() {
    println!("Hello, world!");
}
```
```

### Context Injection

Include files in your prompts for code generation aware of your codebase:

```
@utils.py
@config.json
> Generate tests for the functions in utils.py
```

The utility files are automatically included in the prompt sent to the model.

### Error Handling

All operations include graceful error handling:

- File not found errors
- Permission issues
- Command execution failures
- Ollama connection problems
- Timeout handling

### Clean Output Formatting

- Syntax highlighting for code blocks
- Color-coded messages (info, success, error)
- Organized section headers
- Proper indentation and formatting

## Performance Tips

1. **Use context wisely**: Only include relevant files to keep prompts concise
2. **Model selection**: `deepseek-coder:1.3b` is optimized for code, but you can try other models
3. **Streaming**: Works best for faster feedback; disable with `--no-stream` if needed
4. **Command timeouts**: Default is 30 seconds; adjust in code for long operations

## Troubleshooting

### Docker Compose Issues

#### "dependency failed to start: container codesmith-ollama is unhealthy"

This happens when Docker Compose's health check times out. The fix:

```bash
# Check if Ollama is actually running
docker compose ps

# View Ollama logs to see what's happening
docker compose logs ollama --tail=50

# Try restarting Ollama
docker compose restart ollama

# Clean restart (removes containers but keeps data)
docker compose down
docker compose up -d ollama
docker compose run --rm codesmith-cli

# Full clean (removes everything including volumes)
docker compose down -v
docker compose build
docker compose run --rm codesmith-cli
```

**Why it happens**: 
- Ollama takes longer to start on first run (downloading model)
- Docker health check is too strict
- System resources (disk I/O, CPU) are limiting startup

**CodeSmith handles this during startup**: It waits up to 2 minutes for Ollama to become ready.

### "Cannot connect to Ollama"

Ensure Ollama is running:
```bash
# Check if Ollama is listening
curl http://localhost:11434/api/tags

# Or with docker
docker compose exec ollama curl http://localhost:11434/api/tags
```

### Model not found

The model is checked automatically on CLI startup. If it's not available:

```bash
# Check what's installed
docker compose exec ollama ollama list

# Manually pull if needed
docker compose exec ollama ollama pull deepseek-coder:1.3b
```

### Slow responses

- Reduce context file size
- Use a faster model: `codesmith --model mistral:latest`
- Increase Docker memory allocation (Settings → Resources)
- Reduce temperature for faster inference (in code)

### Permission denied on file operations

Ensure you have write permissions in the working directory:
```bash
chmod 755 ./workspace
ls -la | grep workspace
```

### Port 11434 already in use

Change the port in docker-compose.yml:
```yaml
ports:
  - "11435:11434"  # Change left number to unused port
```

## Architecture Details

### LLM Module (`src/codesmith/llm.py`)

- **OllamaClient**: Manages communication with Ollama API
- **Streaming**: Real-time token generation
- **Error Handling**: Connection validation and timeout management
- **Model Management**: List available models

### Tools Module (`src/codesmith/tools.py`)

- **FileTools**: Read, write, and inspect files
- **ContextInjector**: Embed file contents into prompts

### CLI Module (`src/codesmith/cli.py`)

- **CodeSmithCLI**: Main application class
- **REPL Loop**: Interactive command processing
- **Command Handling**: Dispatch to appropriate handlers
- **Output Formatting**: Color-coded, organized output

## Future Enhancements

- [ ] Code execution sandboxing
- [ ] Multi-file context management
- [ ] Syntax highlighting for output
- [ ] Command history and autocomplete
- [ ] Custom prompt templates
- [ ] Response caching
- [ ] Model fine-tuning support
- [ ] Plugin system for custom commands

## License

MIT License - feel free to use and modify for your needs.

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## Support

For issues, questions, or suggestions, please create an issue in the repository.

---

**Happy coding with CodeSmith!** 🚀
