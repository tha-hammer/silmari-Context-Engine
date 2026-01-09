#!/bin/bash
# Helper script for running Claude Code in Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker Desktop or Docker Engine first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not available${NC}"
    exit 1
fi

# Use docker compose (newer) or docker-compose (older)
COMPOSE_CMD="docker compose"
if ! docker compose version &> /dev/null; then
    COMPOSE_CMD="docker-compose"
fi

# Function to print usage
usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  build       Build the Docker image"
    echo "  up          Start the container"
    echo "  down        Stop the container"
    echo "  shell       Open a bash shell in the container"
    echo "  claude      Run Claude Code interactively"
    echo "  logs        Show container logs"
    echo "  clean       Stop and remove volumes (⚠️  deletes MCP config)"
    echo ""
    echo "Examples:"
    echo "  $0 build              # Build the image"
    echo "  $0 up                # Start container"
    echo "  $0 shell              # Open shell"
    echo "  $0 claude            # Run Claude Code"
    echo "  $0 claude -p 'prompt' # Run Claude with prompt"
}

# Main command handling
case "${1:-}" in
    build)
        echo -e "${GREEN}🔨 Building Docker image...${NC}"
        $COMPOSE_CMD build
        echo -e "${GREEN}✅ Build complete${NC}"
        ;;
    
    up)
        echo -e "${GREEN}🚀 Starting container...${NC}"
        $COMPOSE_CMD up -d
        echo -e "${GREEN}✅ Container started${NC}"
        echo ""
        echo "Access the container with: $0 shell"
        ;;
    
    down)
        echo -e "${YELLOW}🛑 Stopping container...${NC}"
        $COMPOSE_CMD down
        echo -e "${GREEN}✅ Container stopped${NC}"
        ;;
    
    shell)
        echo -e "${GREEN}🐚 Opening shell in container...${NC}"
        $COMPOSE_CMD exec claude-code bash || \
            docker exec -it claude-code-dev bash
        ;;
    
    claude)
        shift  # Remove 'claude' from args
        echo -e "${GREEN}🤖 Running Claude Code...${NC}"
        $COMPOSE_CMD exec claude-code claude "$@" || \
            docker exec -it claude-code-dev claude "$@"
        ;;
    
    logs)
        echo -e "${GREEN}📋 Showing container logs...${NC}"
        $COMPOSE_CMD logs -f claude-code
        ;;
    
    clean)
        echo -e "${YELLOW}⚠️  This will remove all volumes including MCP configuration${NC}"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            $COMPOSE_CMD down -v
            echo -e "${GREEN}✅ Cleaned up${NC}"
        else
            echo "Cancelled"
        fi
        ;;
    
    *)
        usage
        exit 1
        ;;
esac




