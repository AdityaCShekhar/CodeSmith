#!/bin/bash
# Quick start script for CodeSmith

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

compose() {
    if command -v docker-compose &> /dev/null; then
        docker-compose "$@"
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        docker compose "$@"
    else
        echo "Docker Compose is not installed." >&2
        return 127
    fi
}

echo "📦 CodeSmith - Automated Setup"
echo "===================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker and Docker Compose."
    exit 1
fi

echo "✓ Docker is installed"

# Check if Docker Compose is installed
if ! compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi

echo "✓ Docker Compose is installed"
echo ""

echo "🚀 Starting CodeSmith Environment..."
echo ""

# Build Docker image
echo "1️⃣  Building Docker image..."
compose build

echo ""
echo "2️⃣  Starting Ollama service..."
compose up -d ollama

echo ""
echo "⏳ Waiting for Ollama to be ready..."
sleep 5

# Check if Ollama is healthy
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if compose exec ollama curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✓ Ollama is online"
        break
    fi
    sleep 2
    attempt=$((attempt+1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "⚠️  Ollama is taking longer than expected"
    echo "   Continue with: docker compose run --rm codesmith-cli"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Next Steps:"
echo "   - Start the CLI:       codesmith"
echo "   - Or with docker:      docker compose run --rm codesmith-cli"
echo "   - Check status:        docker compose ps"
echo "   - View logs:           docker compose logs ollama"
echo "   - Stop services:       docker compose down"
echo ""
echo "📚 For more info, see README.md"
