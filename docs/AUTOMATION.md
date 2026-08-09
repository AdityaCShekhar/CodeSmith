# CodeSmith Automation Guide

Automate code generation and file creation with CodeSmith!

## Quick Start

### Single File Generation

```bash
# Generate and save a single file
codesmith-batch quicksort.py "Write a Python quicksort implementation"

# Files are saved to current directory
ls -la quicksort.py
```

### Batch Generation (Multiple Files)

```bash
# Generate multiple files from config
codesmith-batch examples/batch_example.json

# Or create your own batch.json
codesmith-batch my_batch.json
```

## Setup

First, ensure you have the automation scripts available:

```bash
# Add to PATH (same as codesmith)
export PATH="/path/to/CodeSmith:$PATH"

# Then from anywhere:
codesmith-batch quicksort.py "Your prompt here"
```

## Usage

### Single File Generation

```bash
codesmith-batch <output_file> "<prompt>"
```

**Examples:**

```bash
# Python sorting algorithm
codesmith-batch quicksort.py "Write quicksort with examples"

# REST API
codesmith-batch api.py "Create Flask REST API with documentation"

# Test suite
codesmith-batch tests.py "Write pytest tests for calculator module"

# Web scraper
codesmith-batch scraper.py "Build web scraper for hacker news"
```

### Batch File Generation

Create a `batch.json` file:

```json
{
  "tasks": [
    {
      "output": "quicksort.py",
      "prompt": "Write a quicksort implementation"
    },
    {
      "output": "mergesort.py",
      "prompt": "Write a merge sort implementation"
    },
    {
      "output": "tests.py",
      "prompt": "Write unit tests for both algorithms"
    }
  ]
}
```

Then run:

```bash
codesmith-batch batch.json
```

## Interactive vs Automated

### Interactive (Manual)
```
codesmith
> Write a function
/write output.py
(paste code, Ctrl+D)
```

### Automated (Fast)
```bash
codesmith-batch output.py "Write a function"
# Done! File saved.
```

## Examples

### Example 1: Generate Multiple Utilities

```bash
# Create batch.json
cat > batch.json << 'EOF'
{
  "tasks": [
    {
      "output": "string_utils.py",
      "prompt": "Create string utility functions: reverse, palindrome check, anagram check"
    },
    {
      "output": "math_utils.py",
      "prompt": "Create math functions: factorial, fibonacci, prime checker"
    },
    {
      "output": "test_utils.py",
      "prompt": "Write comprehensive pytest tests for all utility functions"
    }
  ]
}
EOF

# Generate all at once
codesmith-batch batch.json
```

### Example 2: Generate Project Structure

```bash
# Create multiple project files
codesmith-batch models.py "Create SQLAlchemy models for blog (User, Post, Comment)"
codesmith-batch routes.py "Create Flask routes for CRUD operations"
codesmith-batch tests.py "Write tests for the routes and models"
codesmith-batch requirements.txt "Generate requirements.txt for Flask blog"
```

### Example 3: Data Processing Pipeline

```bash
codesmith-batch data_loader.py "Create functions to load CSV and JSON files"
codesmith-batch data_cleaner.py "Create data cleaning functions for missing values and outliers"
codesmith-batch data_analyzer.py "Create statistical analysis functions"
codesmith-batch pipeline.py "Integrate all components into a complete pipeline"
```

## Advanced Features

### Custom Model

```bash
codesmith-batch myfile.py "Your prompt" --model mistral:latest
```

Convert to batch config:
```json
{
  "tasks": [
    {
      "output": "file1.py",
      "prompt": "First file",
      "model": "mistral:latest"
    },
    {
      "output": "file2.py",
      "prompt": "Second file",
      "model": "deepseek-coder:1.3b"
    }
  ]
}
```

## Workflow Example

```bash
# 1. Create batch configuration
cat > project.json << 'EOF'
{
  "tasks": [
    {"output": "main.py", "prompt": "Main entry point with CLI"},
    {"output": "utils.py", "prompt": "Helper functions"},
    {"output": "config.py", "prompt": "Configuration management"},
    {"output": "tests.py", "prompt": "Unit tests"},
    {"output": "README.md", "prompt": "Project documentation"}
  ]
}
EOF

# 2. Generate all files at once
codesmith-batch project.json

# 3. Review generated code
ls -la *.py

# 4. Test the code
python3 -m pytest tests.py

# 5. Run the application
python3 main.py
```

## Performance Tips

1. **Batch Configuration**: Group related files together
2. **Clear Prompts**: More specific = better code
3. **Smaller Prompts**: Faster generation (simpler tasks)
4. **Model Selection**: Different models for different tasks

## Troubleshooting

### "Ollama not running"
```bash
docker compose up -d ollama
```

### "File not found"
Check you're in the right directory:
```bash
pwd
ls -la batch.json
```

### "Invalid JSON"
Validate your JSON:
```bash
python3 -m json.tool batch.json
```

### Model not available
```bash
docker compose exec ollama ollama list
docker compose exec ollama ollama pull deepseek-coder:1.3b
```

## Batch JSON Schema

```json
{
  "tasks": [
    {
      "output": "filename.ext",    // Required: output file name
      "prompt": "description",      // Required: what to generate
      "model": "model:tag"          // Optional: specific model
    }
  ]
}
```

## Tips & Tricks

### Generate Multiple Variations
```bash
codesmith-batch approach1.py "Implement quicksort using recursion"
codesmith-batch approach2.py "Implement quicksort using iteration"
codesmith-batch approach3.py "Implement quicksort using functional approach"
```

### Create Documentation
```bash
codesmith-batch README.md "Write comprehensive documentation for a Python project"
codesmith-batch API.md "Generate API documentation"
codesmith-batch TUTORIAL.md "Write a beginner's tutorial"
```

### Generate Configuration Files
```bash
codesmith-batch docker-compose.yml "Create docker compose for Python app"
codesmith-batch Dockerfile "Generate production-ready Dockerfile"
codesmith-batch .env.example "Create environment variables template"
```

## Next Steps

1. **Try Single Generation**
   ```bash
   codesmith-batch test.py "Write hello world"
   ```

2. **Create Your First Batch**
   - Create a batch.json
   - Run codesmith-batch batch.json

3. **Integrate Into Workflow**
   - Use in CI/CD pipelines
   - Automate code scaffolding
   - Generate project templates

## Commands Summary

```bash
# Single file
codesmith-batch FILE "PROMPT"

# Batch from JSON
codesmith-batch CONFIG.json

# With custom model
codesmith-batch FILE "PROMPT" --model MODEL

# Help
codesmith-batch --help
```

Happy automating! 🚀
