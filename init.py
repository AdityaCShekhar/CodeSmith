#!/usr/bin/env python3
"""Initialize DeepX and pull models if needed."""

import subprocess
import time
import sys
import os
from pathlib import Path

try:
    import requests
except ImportError:
    # If requests isn't available, try to import urllib
    import urllib.request
    requests = None

def wait_for_ollama(host: str = "http://ollama:11434", timeout: int = 120) -> bool:
    """Wait for Ollama to be ready (with extended timeout)."""
    print(f"⏳ Waiting for Ollama at {host}...")
    start = time.time()
    attempt = 0
    
    while time.time() - start < timeout:
        attempt += 1
        try:
            if requests:
                response = requests.get(f"{host}/api/tags", timeout=5)
                if response.status_code == 200:
                    print("✓ Ollama is ready")
                    return True
            else:
                # Fallback using urllib
                urllib.request.urlopen(f"{host}/api/tags", timeout=5)
                print("✓ Ollama is ready")
                return True
        except Exception as e:
            if attempt % 10 == 0:
                elapsed = int(time.time() - start)
                print(f"  Still waiting... ({elapsed}s elapsed)")
        time.sleep(1)
    
    print("❌ Ollama did not start in time")
    return False

def pull_model(model: str = "deepseek-coder:1.3b", host: str = "http://ollama:11434") -> bool:
    """Pull model if not already available."""
    try:
        print(f"\n📦 Checking for model: {model}")
        
        if not requests:
            print("⚠️  Cannot check model without requests library")
            print("   Starting CLI anyway - model may be pulling in background")
            return True
        
        # Check if model exists
        response = requests.get(f"{host}/api/tags", timeout=10)
        if response.status_code != 200:
            raise Exception(f"API returned {response.status_code}")
        
        models = response.json().get("models", [])
        model_names = [m.get("name", "") for m in models]
        
        # Check if our model is in the list
        if any(model in name for name in model_names):
            print(f"✓ Model '{model}' already available")
            print(f"  Available models: {', '.join(model_names)}")
            return True
        
        print(f"📥 Pulling {model}...")
        print(f"   (This may take 2-5 minutes on first run)")
        
        # Initiate model pull
        response = requests.post(
            f"{host}/api/pull",
            json={"name": model},
            timeout=600,
            stream=True
        )
        
        if response.status_code == 200:
            # Stream the pull progress
            for line in response.iter_lines():
                if line:
                    try:
                        import json
                        data = json.loads(line)
                        if "status" in data and "digest" in data:
                            status = data["status"]
                            if status in ["downloading", "verifying", "writing"]:
                                print(f"   {status}...", end="\r")
                    except:
                        pass
            print(f"✓ Model '{model}' ready               ")
            return True
        else:
            print(f"⚠️  Model pull returned status {response.status_code}")
            print("   Starting CLI anyway - model may be pulling in background")
            return True
            
    except requests.exceptions.Timeout:
        print("⚠️  Model pull timed out")
        print("   Starting CLI anyway - model may still be pulling")
        return True
    except Exception as e:
        print(f"⚠️  Could not verify/pull model: {e}")
        print("   Starting CLI anyway - model may be pulling in background")
        return True

def main():
    """Initialize and launch CLI."""
    ollama_host = os.getenv("OLLAMA_URL", "http://ollama:11434")
    
    print("\n" + "=" * 50)
    print("🚀 DeepX Initialization")
    print("=" * 50)
    
    # Wait for Ollama (extended timeout)
    if not wait_for_ollama(ollama_host, timeout=120):
        print("❌ Cannot connect to Ollama after 2 minutes")
        print(f"   Make sure Ollama is running at {ollama_host}")
        sys.exit(1)
    
    # Pull model (but don't fail if we can't)
    pull_model(host=ollama_host)
    
    print("\n" + "=" * 50)
    print("✅ Ready! Starting CLI...")
    print("=" * 50 + "\n")
    
    # Launch CLI
    try:
        subprocess.run(["python3", "cli.py"], cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Error launching CLI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
