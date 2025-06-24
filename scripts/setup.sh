#!/bin/bash

# Exit on error
set -e

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to print status messages
print_status() {
    echo -e "${GREEN}==>${NC} $1"
}

print_error() {
    echo -e "${RED}Error:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}Warning:${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Check for required tools
check_requirements() {
    print_status "Checking requirements..."
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        print_error "python3 is not installed"
        exit 1
    fi
    
    if ! command -v poetry &> /dev/null; then
        print_error "poetry is not installed"
        exit 1
    fi
}

# Create and setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        print_warning "Created .env file from template. Please update with your settings."
    fi
    
    # Create necessary directories
    mkdir -p "$PROJECT_ROOT/data/postgres"
    mkdir -p "$PROJECT_ROOT/data/redis"
    mkdir -p "$PROJECT_ROOT/data/playwright"
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    cd "$PROJECT_ROOT/packages/mcp_server"
    poetry install
    
    print_status "Installing Playwright browsers..."
    poetry run playwright install chromium
}

# Start Docker services
start_services() {
    print_status "Starting Docker services..."
    cd "$PROJECT_ROOT"
    docker-compose up -d postgres redis
    
    # Wait for PostgreSQL to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    until docker-compose exec -T postgres pg_isready; do
        echo -n "."
        sleep 1
    done
    echo
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    cd "$PROJECT_ROOT/packages/mcp_server"
    poetry run python -m src.mcp_server.scripts.setup
}

# Initialize MCP server
init_server() {
    print_status "Initializing MCP server..."
    cd "$PROJECT_ROOT"
    docker-compose up -d mcp_server
}

# Main setup process
main() {
    print_status "Starting setup process..."
    
    check_docker
    check_requirements
    setup_environment
    install_dependencies
    start_services
    run_migrations
    init_server
    
    print_status "Setup completed successfully!"
    echo -e "\nMCP server is now running at http://localhost:8000"
    echo "API documentation available at http://localhost:8000/docs"
}

# Run main function
main

