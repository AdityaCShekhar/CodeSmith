#!/bin/bash
# Makefile-like commands for DeepX (source this or run commands directly)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Show help
show_help() {
    cat << EOF
${BLUE}DeepX - Available Commands${NC}

Usage: source commands.sh then run commands, or use directly:
  bash commands.sh [command]

${YELLOW}Setup & Initialization${NC}
  setup           - Automated setup with Docker
  build           - Build Docker images
  pull-model      - Pull deepseek-coder model
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
  bash commands.sh setup
  bash commands.sh run

  # Development workflow
  bash commands.sh build
  bash commands.sh start
  bash commands.sh status
  bash commands.sh run

  # Cleanup
  bash commands.sh clean-all

EOF
}

# Setup everything
cmd_setup() {
    echo -e "${BLUE}🚀 Starting DeepX Setup...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found. Please install Docker.${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ Docker installed${NC}"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose not found. Please install Docker Compose.${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
    
    echo -e "${BLUE}Building Docker images...${NC}"
    docker-compose build || return 1
    
    echo -e "${BLUE}Starting Ollama service...${NC}"
    docker-compose up -d ollama || return 1
    
    echo -e "${BLUE}⏳ Waiting for Ollama to be ready...${NC}"
    sleep 10
    
    # Check connection
    if docker-compose exec ollama curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama is healthy${NC}"
    else
        echo -e "${RED}⚠️  Ollama not responding yet, continuing anyway...${NC}"
    fi
    
    echo -e "${BLUE}Pulling model (this may take 2-5 minutes)...${NC}"
    docker-compose exec -T ollama ollama pull deepseek-coder:1.3b || return 1
    
    echo -e "${GREEN}✅ Setup complete!${NC}"
    echo -e "${YELLOW}Next: bash commands.sh run${NC}"
}

# Build Docker images
cmd_build() {
    echo -e "${BLUE}Building Docker images...${NC}"
    docker-compose build
}

# Pull model
cmd_pull_model() {
    echo -e "${BLUE}Pulling deepseek-coder model...${NC}"
    docker-compose exec ollama ollama pull deepseek-coder:1.3b
}

# Initialize (alias for setup)
cmd_init() {
    cmd_setup
}

# Run CLI
cmd_run() {
    echo -e "${BLUE}Starting DeepX CLI...${NC}"
    docker-compose run --rm deepx-cli
}

# Run single prompt
cmd_run_single() {
    local PROMPT="${1:-Write a Python function to calculate factorial}"
    echo -e "${BLUE}Running: $PROMPT${NC}"
    docker-compose run --rm deepx-cli -p "$PROMPT"
}

# Run without streaming
cmd_run_no_stream() {
    echo -e "${BLUE}Starting DeepX CLI (no streaming)...${NC}"
    docker-compose run --rm deepx-cli --no-stream
}

# Start Ollama
cmd_start() {
    echo -e "${BLUE}Starting Ollama service...${NC}"
    docker-compose up -d ollama
    echo -e "${YELLOW}Waiting for Ollama...${NC}"
    sleep 5
    docker-compose logs ollama | tail -5
}

# Stop all services
cmd_stop() {
    echo -e "${BLUE}Stopping all services...${NC}"
    docker-compose down
}

# Restart services
cmd_restart() {
    echo -e "${BLUE}Restarting services...${NC}"
    docker-compose restart
}

# View logs
cmd_logs() {
    docker-compose logs -f
}

# View Ollama logs
cmd_logs_ollama() {
    docker-compose logs -f ollama
}

# Show process status
cmd_ps() {
    docker-compose ps
}

# Clean containers
cmd_clean() {
    echo -e "${YELLOW}Removing containers...${NC}"
    docker-compose down
    echo -e "${GREEN}✓ Cleaned${NC}"
}

# Clean everything
cmd_clean_all() {
    echo -e "${RED}⚠️  Removing containers, images, and volumes...${NC}"
    docker-compose down -v --rmi all
    echo -e "${GREEN}✓ Deep clean complete${NC}"
}

# Run demo
cmd_demo() {
    echo -e "${BLUE}Running demonstration...${NC}"
    python3 demo.py
}

# Shell into CLI
cmd_shell_cli() {
    echo -e "${BLUE}Opening shell in CLI container...${NC}"
    docker-compose exec deepx-cli /bin/sh
}

# Shell into Ollama
cmd_shell_ollama() {
    echo -e "${BLUE}Opening shell in Ollama container...${NC}"
    docker-compose exec ollama /bin/bash
}

# Test connection
cmd_test_connection() {
    echo -e "${BLUE}Testing Ollama connection...${NC}"
    curl -s http://localhost:11434/api/tags | python3 -m json.tool
}

# List models
cmd_list_models() {
    echo -e "${BLUE}Available models:${NC}"
    docker-compose exec ollama ollama list
}

# Inspect resources
cmd_inspect() {
    echo -e "${BLUE}=== Docker Images ===${NC}"
    docker images | grep deepx
    echo -e "\n${BLUE}=== Running Containers ===${NC}"
    docker-compose ps
    echo -e "\n${BLUE}=== Container Details ===${NC}"
    docker-compose exec ollama ollama list
}

# Show status
cmd_status() {
    echo -e "${BLUE}=== DeepX Status ===${NC}"
    echo -e "\n${BLUE}Containers:${NC}"
    docker-compose ps
    
    if docker-compose exec ollama curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "\n${GREEN}✓ Ollama is online${NC}"
        echo -e "\n${BLUE}Models:${NC}"
        docker-compose exec ollama ollama list
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
