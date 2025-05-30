#!/bin/bash
set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored status messages
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
check_requirements() {
    log_info "Checking required tools..."
    
    local missing_tools=()
    
    # Check for Python
    if ! command_exists python3; then
        missing_tools+=("python3")
    fi
    
    # Check for Poetry
    if ! command_exists poetry; then
        missing_tools+=("poetry")
    fi
    
    # Check for Node.js
    if ! command_exists node; then
        missing_tools+=("nodejs")
    fi
    
    # Check for npm
    if ! command_exists npm; then
        missing_tools+=("npm")
    fi
    
    # Check for PostgreSQL client
    if ! command_exists psql; then
        missing_tools+=("postgresql-client")
    fi
    
    # If any tools are missing, print error and exit
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "The following required tools are missing:"
        printf '%s\n' "${missing_tools[@]}"
        echo
        log_info "Please install them using your package manager:"
        echo "sudo apt-get install ${missing_tools[*]}"
        exit 1
    fi
    
    log_success "All required tools are installed!"
}

# Setup Python virtual environment
setup_venv() {
    log_info "Setting up Python virtual environment..."
    
    # Create venv if it doesn't exist
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        log_success "Created virtual environment"
    else
        log_warning "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Upgrade pip
    python3 -m pip install --upgrade pip
    
    log_success "Virtual environment is ready!"
}

# Install dependencies with Poetry
install_dependencies() {
    log_info "Installing project dependencies..."
    
    # Install dependencies with Poetry
    poetry install
    
    log_success "Dependencies installed successfully!"
}

# Install and configure Playwright
setup_playwright() {
    log_info "Setting up Playwright..."
    
    # Install Playwright globally
    npm install -g playwright@1.40.0
    
    # Install Chromium browser and dependencies
    playwright install chromium
    playwright install-deps chromium
    
    log_success "Playwright setup complete!"
}

# Setup pre-commit hooks
setup_git_hooks() {
    log_info "Setting up Git hooks..."
    
    # Install pre-commit if not already installed
    if ! command_exists pre-commit; then
        pip install pre-commit
    fi
    
    # Install the pre-commit hooks
    pre-commit install
    
    # Create .pre-commit-config.yaml if it doesn't exist
    if [ ! -f ".pre-commit-config.yaml" ]; then
        cat > .pre-commit-config.yaml << 'EOF'
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
    -   id: check-added-large-files
    -   id: check-json
    -   id: check-toml
    -   id: detect-private-key

-   repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
    -   id: black

-   repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
    -   id: isort

-   repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
    -   id: flake8
EOF
    fi
    
    log_success "Git hooks configured!"
}

# Initialize development database
setup_database() {
    log_info "Setting up development database..."
    
    # Check if database already exists
    if psql -lqt | cut -d \| -f 1 | grep -qw "mcp_dev"; then
        log_warning "Database 'mcp_dev' already exists"
    else
        # Create development database
        createdb mcp_dev
        log_success "Created database 'mcp_dev'"
    fi
    
    # Run migrations
    log_info "Running database migrations..."
    poetry run alembic upgrade head
    
    log_success "Database setup complete!"
}

# Create necessary directories
setup_directories() {
    log_info "Creating project directories..."
    
    # Create required directories
    mkdir -p \
        data/assets \
        data/cache \
        data/playwright \
        logs
    
    # Set permissions
    chmod -R 755 data logs
    
    log_success "Directories created and configured!"
}

# Create local configuration
create_local_config() {
    log_info "Creating local configuration..."
    
    if [ ! -f ".env" ]; then
        cat > .env << 'EOF'
# Development configuration
DEBUG=true
ENVIRONMENT=development

# Server settings
PORT=8000
WORKERS=1
LOG_LEVEL=DEBUG

# Database settings
DATABASE_URL=postgresql://localhost/mcp_dev

# Redis settings
REDIS_URL=redis://localhost:6379/0

# Playwright settings
PLAYWRIGHT_BROWSERS_PATH=./data/playwright
EOF
        log_success "Created .env file with default configuration"
    else
        log_warning ".env file already exists"
    fi
}

# Main setup process
main() {
    echo "=== MCP Server Development Environment Setup ==="
    echo
    
    # Run all setup steps
    check_requirements
    setup_venv
    install_dependencies
    setup_playwright
    setup_git_hooks
    setup_database
    setup_directories
    create_local_config
    
    echo
    log_success "Development environment setup complete!"
    echo
    log_info "To start developing:"
    echo "1. Activate the virtual environment: source .venv/bin/activate"
    echo "2. Start the development server: poetry run uvicorn mcp_server.api.main:app --reload"
    echo
    log_info "Happy coding! 🚀"
}

# Run main setup
main

