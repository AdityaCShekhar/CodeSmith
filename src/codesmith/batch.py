#!/usr/bin/env python3
"""
CodeSmith Batch Generation Script
Automate bulk code generation and file saving
"""

import sys
import json
import argparse
import os
from pathlib import Path

from .llm import OllamaClient
from .tools import FileTools

def generate_single(output_file: str, prompt: str, model: str = "qwen3", ollama_url: str = None) -> bool:
    """Generate code and save to file."""
    try:
        client = OllamaClient(
            ollama_url or os.getenv("OLLAMA_URL", "http://localhost:11434"),
            model,
        )
        
        print(f"\n📝 {output_file}")
        print(f"   Prompt: {prompt[:60]}...")
        
        # Generate code
        code = client.generate(prompt, stream=False)
        
        # Save to file
        FileTools.write_file(output_file, code)
        print(f"   ✓ Saved ({len(code)} bytes)")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

def generate_from_json(json_file: str, default_model: str) -> None:
    """Generate multiple files from JSON config."""
    try:
        with open(json_file) as f:
            config = json.load(f)
        
        tasks = config.get("tasks", [])
        if not tasks:
            print("Error: No tasks in JSON file")
            sys.exit(1)
        
        print(f"📦 Running {len(tasks)} generation tasks...\n")
        
        success = 0
        failed = 0
        
        for task in tasks:
            output = task.get("output")
            prompt = task.get("prompt")
            model = task.get("model", default_model)
            
            if not output or not prompt:
                print("✗ Invalid task (missing 'output' or 'prompt')")
                failed += 1
                continue
            
            if generate_single(output, prompt, model=model):
                success += 1
            else:
                failed += 1
        
        print(f"\n✅ Completed: {success} succeeded, {failed} failed")
        
    except FileNotFoundError:
        print(f"Error: File not found: {json_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {json_file}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="CodeSmith Batch Code Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file
  codesmith-batch quicksort.py "Write a quicksort function"
  
  # From JSON config
  codesmith-batch batch.json
  
JSON Format:
  {
    "tasks": [
      {
        "output": "quicksort.py",
        "prompt": "Write a quicksort implementation"
      },
      {
        "output": "api.py", 
        "prompt": "Create a Flask REST API"
      }
    ]
  }
        """
    )
    
    parser.add_argument(
        "input",
        help="Output filename or JSON config file"
    )
    
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Generation prompt (optional if using JSON)"
    )
    
    parser.add_argument(
        "--model",
        default="qwen3",
        help="Model to use (default: qwen3)"
    )
    
    args = parser.parse_args()
    
    # Check if input is JSON or filename
    if args.input.endswith(".json"):
        generate_from_json(args.input, args.model)
    else:
        if not args.prompt:
            print("Error: Prompt required when not using JSON")
            print("Usage: codesmith-batch <output_file> \"<prompt>\"")
            sys.exit(1)
        
        if generate_single(args.input, args.prompt, args.model):
            sys.exit(0)
        else:
            sys.exit(1)

if __name__ == "__main__":
    main()
