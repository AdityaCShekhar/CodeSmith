#!/bin/bash
# Makefile-like commands for CodeSmith (source this or run commands directly)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYTHONPATH="$PROJECT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

compose() {
    if command -v docker-compose &> /dev/null; then
        docker-compose -f "$PROJECT_DIR/docker-compose.yml" "$@"
    elif command -v docker &> /dev/null && docker compose version &> /dev/null; then
        docker compose -f "$PROJECT_DIR/docker-compose.yml" "$@"
    else
        echo "Docker Compose is not installed." >&2
        return 127
    fi
}

# Show help
show_help() {
    cat << EOF
${BLUE}CodeSmith - Available Commands${NC}

Usage: source scripts/commands.sh then run commands, or use directly:
  bash scripts/commands.sh [command]

${YELLOW}Setup & Initialization${NC}
  setup           - Automated setup with Docker
  build           - Build Docker images
  pull-model      - Show OpenRouter model information
  init            - Full initialization

${YELLOW}Running the CLI${NC}
  run             - Start CLI interactive mode
  run-single      - Run single command (edit PROMPT in script)
  run-no-stream   - Run without streaming

${YELLOW}Docker Management${NC}
  start           - Start the CodeSmith container
  stop            - Stop all services
  restart         - Restart services
  logs            - View service logs
  ps              - Show running processes
  clean           - Stop and remove containers
  clean-all       - Stop, remove containers, AND volumes

${YELLOW}Development & Testing${NC}
  demo            - Run demonstration script
  shell-cli       - SSH into CLI container
  inspect         - Inspect Docker images and containers

${YELLOW}Utilities${NC}
  help            - Show this help message
  status          - Show system status

${YELLOW}Examples${NC}
  # Basic startup
  bash scripts/commands.sh setup
  bash scripts/commands.sh run

  # Development workflow
  bash scripts/commands.sh build
  bash scripts/commands.sh start
  bash scripts/commands.sh status
  bash scripts/commands.sh run

  # Cleanup
  bash scripts/commands.sh clean-all

EOF
}

# Setup everything
cmd_setup() {
    echo -e "${BLUE}🚀 Starting CodeSmith Setup...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found. Please install Docker.${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ Docker installed${NC}"
    
    # Check Docker Compose
    if ! compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose not found. Please install Docker Compose.${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
    
    echo -e "${BLUE}Building Docker images...${NC}"
    compose build || return 1
    
    if [ -z "${OPENROUTER_API_KEY:-}" ]; then
        echo -e "${RED}❌ OPENROUTER_API_KEY is not set.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Setup complete!${NC}"
    echo -e "${YELLOW}Next: bash scripts/commands.sh run${NC}"
}

# Build Docker images
cmd_build() {
    echo -e "${BLUE}Building Docker images...${NC}"
    compose build
}

# Pull model
cmd_pull_model() {
    echo -e "${YELLOW}OpenRouter models are hosted remotely; no local model pull is required.${NC}"
}

# Initialize (alias for setup)
cmd_init() {
    cmd_setup
}

# Run CLI
cmd_run() {
    echo -e "${BLUE}Starting CodeSmith CLI...${NC}"
    compose run --rm codesmith-cli
}

# Run single prompt
cmd_run_single() {
    local PROMPT="${1:-Write a Python function to calculate factorial}"
    echo -e "${BLUE}Running: $PROMPT${NC}"
    compose run --rm codesmith-cli -p "$PROMPT"
}

# Run without streaming
cmd_run_no_stream() {
    echo -e "${BLUE}Starting CodeSmith CLI (no streaming)...${NC}"
    compose run --rm codesmith-cli --no-stream
}

# Start the CodeSmith container
cmd_start() {
    echo -e "${BLUE}Starting CodeSmith...${NC}"
    compose run --rm codesmith-cli
}

# Stop all services
cmd_stop() {
    echo -e "${BLUE}Stopping all services...${NC}"
    compose down
}

# Restart services
cmd_restart() {
    echo -e "${BLUE}Restarting services...${NC}"
    compose restart
}

# View logs
cmd_logs() {
    compose logs -f
}

# Retained command for compatibility with older scripts.
cmd_logs_ollama() {
    echo -e "${YELLOW}Ollama is no longer used; CodeSmith uses OpenRouter.${NC}"
}

# Show process status
cmd_ps() {
    compose ps
}

# Clean containers
cmd_clean() {
    echo -e "${YELLOW}Removing containers...${NC}"
    compose down
    echo -e "${GREEN}✓ Cleaned${NC}"
}

# Clean everything
cmd_clean_all() {
    echo -e "${RED}⚠️  Removing containers, images, and volumes...${NC}"
    compose down -v --rmi all
    echo -e "${GREEN}✓ Deep clean complete${NC}"
}

# Run demo
cmd_demo() {
    echo -e "${BLUE}Running demonstration...${NC}"
    python3 "$PROJECT_DIR/examples/demo.py"
}

# Shell into CLI
cmd_shell_cli() {
    echo -e "${BLUE}Opening shell in CLI container...${NC}"
    compose exec codesmith-cli /bin/sh
}

# Retained command for compatibility with older scripts.
cmd_shell_ollama() {
    echo -e "${YELLOW}Ollama is no longer used; use shell-cli instead.${NC}"
}

# Test connection
cmd_test_connection() {
    echo -e "${BLUE}Testing OpenRouter configuration...${NC}"
    test -n "${OPENROUTER_API_KEY:-}" && echo -e "${GREEN}✓ OPENROUTER_API_KEY is set${NC}" || echo -e "${RED}✗ OPENROUTER_API_KEY is not set${NC}"
}

# List models
cmd_list_models() {
    echo -e "${BLUE}Default model: openai/gpt-oss-20b:free${NC}"
}

# Inspect resources
cmd_inspect() {
    echo -e "${BLUE}=== Docker Images ===${NC}"
    docker images | grep codesmith
    echo -e "\n${BLUE}=== Running Containers ===${NC}"
    compose ps
    echo -e "\n${BLUE}=== Container Details ===${NC}"
    echo -e "${BLUE}Model provider: OpenRouter${NC}"
}

# Show status
cmd_status() {
    echo -e "${BLUE}=== CodeSmith Status ===${NC}"
    echo -e "\n${BLUE}Containers:${NC}"
    compose ps
    
    if [ -n "${OPENROUTER_API_KEY:-}" ]; then
        echo -e "\n${GREEN}✓ OpenRouter API key is configured${NC}"
    else
        echo -e "\n${RED}✗ OPENROUTER_API_KEY is not set${NC}"
    fi
}

# Main dispatcher
main() {
    local cmd="${1:-help}"
    
    case "$cmd" in
        setup)              cmd_setup ;;
        build)              cmd_build ;;
        pull-model)         cmd_pull_model ;;
        init)               cmd_init ;;
        run)                cmd_run ;;
        run-single)         cmd_run_single "${2}" ;;
        run-no-stream)      cmd_run_no_stream ;;
        start)              cmd_start ;;
        stop)               cmd_stop ;;
        restart)            cmd_restart ;;
        logs)               cmd_logs ;;
        logs-ollama)        cmd_logs_ollama ;;
        ps)                 cmd_ps ;;
        clean)              cmd_clean ;;
        clean-all)          cmd_clean_all ;;
        demo)               cmd_demo ;;
        shell-cli)          cmd_shell_cli ;;
        shell-ollama)       cmd_shell_ollama ;;
        test-connection)    cmd_test_connection ;;
        list-models)        cmd_list_models ;;
        inspect)            cmd_inspect ;;
        status)             cmd_status ;;
        help|-h|--help)     show_help ;;
        *)
            echo -e "${RED}Unknown command: $cmd${NC}"
            show_help
            exit 1
            ;;
    esac
}

# Only run main if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
