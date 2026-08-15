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

if [ -z "${OPENROUTER_API_KEY:-}" ]; then
    echo "❌ OPENROUTER_API_KEY is not set. Export it before running setup."
    exit 1
fi

echo "🚀 Starting CodeSmith Environment..."
echo ""

# Build Docker image
echo "1️⃣  Building Docker image..."
compose build

echo ""
echo "2️⃣  OpenRouter API key detected"

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Next Steps:"
echo "   - Start the CLI:       codesmith"
echo "   - Or with docker:      docker compose run --rm codesmith-cli"
echo "   - Check status:        docker compose ps"
echo "   - Set model:           docker compose run --rm codesmith-cli --model openai/gpt-oss-20b:free"
echo "   - Stop services:       docker compose down"
echo ""
echo "📚 For more info, see README.md"
