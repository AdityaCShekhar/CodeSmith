# CodeSmith - Architecture & Implementation Guide

## Project Structure

```
CodeSmith/
├── cli.py                  # Main CLI application (entry point)
├── llm.py                  # Ollama API client
├── tools.py                # File and shell utilities
├── demo.py                 # Usage demonstration
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Container orchestration
├── setup.sh                # Automated setup script
├── .gitignore              # Git ignore rules
└── README.md               # Complete documentation
```

## Module Design

### 1. CLI Module (`cli.py`)

**Purpose**: Main application interface with REPL loop and command handling.

**Key Classes**:
- `CodexCLI`: Main application class
  - Initialization & Ollama connection
  - REPL loop management
  - Command dispatching
  - Output formatting

**Key Methods**:
- `handle_generate()`: Generate code from prompts
- `handle_write()`: Write user input to files
- `handle_read()`: Display file contents
- `handle_run()`: Execute shell commands
- `handle_context()`: Manage context files
- `repl()`: Main interactive loop

**Features**:
- Color-coded output (info, success, error)
- Keyboard interrupt handling
- Error recovery
- Command-line argument parsing

### 2. LLM Module (`llm.py`)

**Purpose**: Abstract Ollama API interactions with streaming support.

**Key Classes**:
- `OllamaClient`: Ollama API wrapper
  - Connection verification
  - Streaming generation
  - Non-streaming generation
  - Model listing

**Key Methods**:
- `generate()`: Main generation method (streaming or full)
- `_generate_stream()`: Streaming implementation
- `_generate_full()`: Complete response gathering
- `list_models()`: List available models
- `_verify_connection()`: Test Ollama availability

**Features**:
- Automatic connection verification
- Streaming with token-by-token output
- Configurable temperature and top-p sampling
- Graceful error handling with detailed messages
- Timeout management (120 seconds)

### 3. Tools Module (`tools.py`)

**Purpose**: File operations, shell execution, and context management.

**Key Classes**:
- `FileTools`: File system operations
  - Read files safely
  - Write files with directory creation
  - Get file information
  
- `ShellTools`: Command execution
  - Run commands with output capture
  - Timeout handling
  - Safe command execution with formatted output
  
- `ContextInjector`: Embed file content in prompts
  - Read and inject multiple files
  - Error handling for missing files
  - Context prefix formatting

**Features**:
- Exception-based error handling
- Path resolution to absolute paths
- Directory auto-creation
- Command timeout protection (30 seconds)
- Formatted output with STDOUT/STDERR separation

## Data Flow

### Code Generation Flow

```
User Input
    ↓
CLI Command Parser
    ├→ Regular Prompt
    │   └→ ContextInjector (if context files)
    │       └→ OllamaClient.generate()
    │           ├→ Streaming: Token streaming + display
    │           └→ Non-streaming: Full response
    │               └→ Display formatted output
    │
    ├→ /write command
    │   └→ FileTools.write_file()
    │       └→ Display success message
    │
    ├→ /read command
    │   └→ FileTools.read_file()
    │       └→ Display file content
    │
    └→ /run command
        └→ ShellTools.run_command()
            └→ Display output
```

### Context Injection Flow

```
User adds context: /context add file.py
    ↓
FileTools.read_file() - Verify file exists
    ↓
Store filepath in context_files list
    ↓
When generating:
    ├→ ContextInjector.inject_files()
    │   └→ Read all context files
    │   └→ Format as file listings
    │   └→ Prepend to user prompt
    │       └→ Enhanced prompt to Ollama
```

## API Integration

### Ollama API Endpoints Used

1. **Connection Verification**
   ```
   GET /api/tags
   ```
   Lists available models and verifies server is running.

2. **Code Generation (Streaming)**
   ```
   POST /api/generate
   Content-Type: application/json
   
   {
     "model": "deepseek-coder:1.3b",
     "prompt": "...",
     "stream": true,
     "options": {
       "temperature": 0.7,
       "top_p": 0.9
     }
   }
   ```
   Response: Server-sent events with token chunks

3. **Code Generation (Full)**
   ```
   POST /api/generate
   Content-Type: application/json
   
   {
     "model": "deepseek-coder:1.3b",
     "prompt": "...",
     "stream": false,
     "options": {
       "temperature": 0.7,
       "top_p": 0.9
     }
   }
   ```
   Response: JSON with complete response

## Configuration

### Environment Variables

- `OLLAMA_URL`: Ollama server URL (default: `http://ollama:11434`)
- `OLLAMA_MODEL`: Model name (default: `deepseek-coder:1.3b`)

### Command-Line Arguments

```
--url, -u       Ollama server URL
--model, -m     Model name
--prompt, -p    Single prompt (non-interactive mode)
--no-stream     Disable streaming mode
```

## Error Handling Strategy

### Connection Errors
- Connection refused: Suggests Ollama isn't running
- Timeout: Suggests server is slow or unresponsive
- All with clear error messages and hints

### File Operations
- File not found: Explicit error with filepath
- Permission denied: Suggests permission issue
- Directory creation: Automatic on write

### Command Execution
- Non-zero exit codes: Displayed with STDOUT/STDERR
- Timeout: Stops after 30 seconds with message
- Exception: Wrapped in user-friendly message

## Performance Considerations

1. **Streaming Mode**: 
   - Better for UX (immediate feedback)
   - Lower latency for response start
   - Slightly higher overhead per token

2. **Context Size**:
   - Keep context files minimal
   - Each file adds to prompt length
   - Model has 2K token context window (typically)

3. **Model Selection**:
   - `deepseek-coder:1.3b`: Fast, good for code
   - Adjust based on hardware capabilities
   - Trade-off between speed and quality

4. **Timeouts**:
   - Generation: 120 seconds (2 minutes)
   - Shell commands: 30 seconds
   - Ollama requests: 5-10 seconds

## Security Considerations

1. **File Operations**:
   - Paths resolved to absolute paths
   - No symbolic link traversal bypass
   - Directory creation safe (mkdir -p equivalent)

2. **Shell Execution**:
   - Direct shell=True (not sandboxed)
   - Timeout prevents infinite loops
   - Output fully captured before display

3. **Ollama Integration**:
   - Local network only (docker-compose)
   - No authentication in base setup
   - Add firewall rules in production

## Extension Points

### Adding New Commands

1. Add handler method to `CodexCLI` class
2. Add condition in `repl()` method
3. Call handler with parsed arguments

Example:
```python
elif command == "translate":
    if args:
        self.handle_translate(args)
```

### Adding New Tools

1. Create new class in `tools.py`
2. Add instance method to `CodexCLI`
3. Integrate in REPL loop

### Custom Models

Change model in initialization:
```python
cli = CodexCLI(model="your-model:tag")
```

## Testing Recommendations

1. **Unit Tests**: Test individual functions in isolation
2. **Integration Tests**: Test with real Ollama instance
3. **E2E Tests**: Full workflows through CLI
4. **Stress Tests**: Large files, long prompts, rapid commands

## Deployment Considerations

### Docker Deployment
- Use `docker-compose` for all services
- Mount volumes for persistent data
- Network isolation via compose networks

### Local Deployment
- Ensure Ollama is running and accessible
- Python 3.8+ required
- Install dependencies: `pip install -r requirements.txt`

### Health Checks
- Ollama API validation in `_verify_connection()`
- Graceful error messages on failure
- Automatic retry with backoff not implemented (can add)

## Monitoring & Logging

Currently uses print statements. For production:
1. Add logging module
2. Configure different log levels
3. Log to file for debugging
4. Add performance metrics

## Future Enhancement Ideas

1. **Advanced Features**:
   - Code syntax highlighting
   - Multi-file editing
   - Git integration
   - Auto-completion

2. **Performance**:
   - Response caching
   - Prompt compression
   - Parallel generation

3. **UX**:
   - Command history
   - Readline support
   - Interactive file browser

4. **Integration**:
   - VS Code extension
   - GitHub Actions step
   - CI/CD pipeline integration

---

## Quick Reference

### Starting the CLI
```bash
# Interactive mode
python3 cli.py

# Single prompt
python3 cli.py -p "Write factorial function"

# Custom Ollama URL
python3 cli.py --url http://localhost:11434
```

### Common Workflows

**Generate and Save**
```
/read existing_code.py
> Optimize the performance of this code
/write optimized_code.py
```

**Test Generated Code**
```
> Generate a pytest for calculating primes
/write test_primes.py
/run pytest test_primes.py -v
```

**Iterative Development**
```
/context add main.py
> Explain the main.py code
> Generate docstrings for all functions
/write main_documented.py
```

---

For more details, see README.md
