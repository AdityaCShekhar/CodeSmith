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
  pull-model      - Pull qwen3 model
  init            - Full initialization

${YELLOW}Running the CLI${NC}
  run             - Start CLI interactive mode
  run-single      - Run single command (edit PROMPT in script)
  run-no-stream   - Run without streaming

${YELLOW}Docker Management${NC}
  start           - Start Ollama service
  stop            - Stop all services
  restart         - Restart services
  logs            - View service logs
  logs-ollama     - View Ollama logs only
  ps              - Show running processes
  clean           - Stop and remove containers
  clean-all       - Stop, remove containers, AND volumes

${YELLOW}Development & Testing${NC}
  demo            - Run demonstration script
  shell-cli       - SSH into CLI container
  shell-ollama    - SSH into Ollama container
  test-connection - Test Ollama connection
  list-models     - List available models
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
    
    echo -e "${BLUE}Starting Ollama service...${NC}"
    compose up -d ollama || return 1
    
    echo -e "${BLUE}⏳ Waiting for Ollama to be ready...${NC}"
    sleep 10
    
    # Check connection
    if compose exec ollama curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama is healthy${NC}"
    else
        echo -e "${RED}⚠️  Ollama not responding yet, continuing anyway...${NC}"
    fi
    
    echo -e "${BLUE}Pulling model (this may take 2-5 minutes)...${NC}"
    compose exec -T ollama ollama pull qwen3 || return 1
    
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
    echo -e "${BLUE}Pulling qwen3 model...${NC}"
    compose exec ollama ollama pull qwen3
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

# Start Ollama
cmd_start() {
    echo -e "${BLUE}Starting Ollama service...${NC}"
    compose up -d ollama
    echo -e "${YELLOW}Waiting for Ollama...${NC}"
    sleep 5
    compose logs ollama | tail -5
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

# View Ollama logs
cmd_logs_ollama() {
    compose logs -f ollama
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

# Shell into Ollama
cmd_shell_ollama() {
    echo -e "${BLUE}Opening shell in Ollama container...${NC}"
    compose exec ollama /bin/bash
}

# Test connection
cmd_test_connection() {
    echo -e "${BLUE}Testing Ollama connection...${NC}"
    curl -s http://localhost:11434/api/tags | python3 -m json.tool
}

# List models
cmd_list_models() {
    echo -e "${BLUE}Available models:${NC}"
    compose exec ollama ollama list
}

# Inspect resources
cmd_inspect() {
    echo -e "${BLUE}=== Docker Images ===${NC}"
    docker images | grep codesmith
    echo -e "\n${BLUE}=== Running Containers ===${NC}"
    compose ps
    echo -e "\n${BLUE}=== Container Details ===${NC}"
    compose exec ollama ollama list
}

# Show status
cmd_status() {
    echo -e "${BLUE}=== CodeSmith Status ===${NC}"
    echo -e "\n${BLUE}Containers:${NC}"
    compose ps
    
    if compose exec ollama curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "\n${GREEN}✓ Ollama is online${NC}"
        echo -e "\n${BLUE}Models:${NC}"
        compose exec ollama ollama list
    else
        echo -e "\n${RED}✗ Ollama is offline${NC}"
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
