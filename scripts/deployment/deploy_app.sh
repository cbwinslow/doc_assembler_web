#!/bin/bash

# DocAssembler Application Deployment Script
# Automates the deployment of the DocAssembler application to servers

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Default configuration
ENVIRONMENT="${ENVIRONMENT:-production}"
DEPLOY_USER="${DEPLOY_USER:-opc}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/docassembler}"
SERVICE_NAME="${SERVICE_NAME:-docassembler}"
BACKUP_ENABLED="${BACKUP_ENABLED:-true}"
ROLLBACK_ENABLED="${ROLLBACK_ENABLED:-true}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[DEPLOY]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS] SERVER_IP"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -e, --environment ENV   Deployment environment (default: production)"
    echo "  -u, --user USER         Deploy user (default: opc)"
    echo "  -p, --path PATH         Deploy path (default: /opt/docassembler)"
    echo "  -s, --service NAME      Service name (default: docassembler)"
    echo "  --no-backup             Skip backup before deployment"
    echo "  --no-rollback           Disable rollback capability"
    echo "  --force                 Skip confirmation prompts"
    echo ""
    echo "Arguments:"
    echo "  SERVER_IP               IP address of the target server"
    echo ""
    echo "Examples:"
    echo "  $0 192.168.1.100"
    echo "  $0 --environment staging --user ubuntu 10.0.0.50"
    echo "  $0 --no-backup --force 192.168.1.100"
}

# Parse command line arguments
FORCE=false
SERVER_IP=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -u|--user)
            DEPLOY_USER="$2"
            shift 2
            ;;
        -p|--path)
            DEPLOY_PATH="$2"
            shift 2
            ;;
        -s|--service)
            SERVICE_NAME="$2"
            shift 2
            ;;
        --no-backup)
            BACKUP_ENABLED=false
            shift
            ;;
        --no-rollback)
            ROLLBACK_ENABLED=false
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            if [ -z "$SERVER_IP" ]; then
                SERVER_IP="$1"
            else
                print_error "Unknown option: $1"
                usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate server IP
if [ -z "$SERVER_IP" ]; then
    print_error "Server IP not specified"
    usage
    exit 1
fi

# Check SSH connectivity
print_info "Testing SSH connection to $DEPLOY_USER@$SERVER_IP..."
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$DEPLOY_USER@$SERVER_IP" "echo 'SSH connection successful'" >/dev/null 2>&1; then
    print_error "Cannot connect to $DEPLOY_USER@$SERVER_IP via SSH"
    echo "Please ensure:"
    echo "1. The server is accessible"
    echo "2. SSH key authentication is set up"
    echo "3. The user has appropriate permissions"
    exit 1
fi

print_status "Starting deployment to $SERVER_IP..."
print_info "Environment: $ENVIRONMENT"
print_info "Deploy path: $DEPLOY_PATH"
print_info "Service name: $SERVICE_NAME"

# Confirmation prompt
if [ "$FORCE" != true ]; then
    echo ""
    echo "Deployment configuration:"
    echo "  Server: $DEPLOY_USER@$SERVER_IP"
    echo "  Environment: $ENVIRONMENT"
    echo "  Deploy path: $DEPLOY_PATH"
    echo "  Backup enabled: $BACKUP_ENABLED"
    echo "  Rollback enabled: $ROLLBACK_ENABLED"
    echo ""
    read -p "Continue with deployment? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_warning "Deployment cancelled by user"
        exit 0
    fi
fi

# Create deployment timestamp
DEPLOY_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RELEASE_DIR="$DEPLOY_PATH/releases/$DEPLOY_TIMESTAMP"

print_status "Creating deployment directory structure..."

# Create deployment directories on server
ssh "$DEPLOY_USER@$SERVER_IP" "
    sudo mkdir -p $DEPLOY_PATH/{releases,shared,backup}
    sudo mkdir -p $DEPLOY_PATH/shared/{logs,data,uploads,config}
    sudo chown -R $DEPLOY_USER:$DEPLOY_USER $DEPLOY_PATH
"

# Backup current deployment if exists
if [ "$BACKUP_ENABLED" = true ]; then
    print_status "Creating backup of current deployment..."
    ssh "$DEPLOY_USER@$SERVER_IP" "
        if [ -L $DEPLOY_PATH/current ]; then
            CURRENT_RELEASE=\$(readlink $DEPLOY_PATH/current)
            if [ -d \"\$CURRENT_RELEASE\" ]; then
                sudo cp -r \"\$CURRENT_RELEASE\" \"$DEPLOY_PATH/backup/backup_$DEPLOY_TIMESTAMP\"
                echo 'Backup created at $DEPLOY_PATH/backup/backup_$DEPLOY_TIMESTAMP'
            fi
        fi
    "
fi

# Build application locally
print_status "Building application..."
cd "$PROJECT_ROOT"

# Build frontend
print_info "Building frontend..."
cd packages/frontend
npm ci
npm run build
cd "$PROJECT_ROOT"

# Install backend dependencies
print_info "Preparing backend..."
cd apps/backend
npm ci
npm run build 2>/dev/null || echo "Build step skipped (no build script)"
cd "$PROJECT_ROOT"

# Create deployment package
print_status "Creating deployment package..."
TEMP_DEPLOY_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DEPLOY_DIR" EXIT

# Copy application files
cp -r apps/backend/* "$TEMP_DEPLOY_DIR/"
mkdir -p "$TEMP_DEPLOY_DIR/public"
cp -r packages/frontend/dist/* "$TEMP_DEPLOY_DIR/public/"

# Copy configuration files
cp infrastructure/docker/docker-compose.prod.yml "$TEMP_DEPLOY_DIR/docker-compose.yml" 2>/dev/null || \
cp docker-compose.yml "$TEMP_DEPLOY_DIR/" 2>/dev/null || \
echo "No docker-compose file found"

# Copy database scripts
mkdir -p "$TEMP_DEPLOY_DIR/scripts"
cp -r scripts/database "$TEMP_DEPLOY_DIR/scripts/"

# Create environment file template
cat > "$TEMP_DEPLOY_DIR/.env.example" << EOF
# DocAssembler Environment Configuration
NODE_ENV=$ENVIRONMENT
PORT=3000
HOST=0.0.0.0

# Database Configuration
DATABASE_URL=postgresql://docassembler_user:Temp1234!@localhost:5432/docassembler
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET=change-this-in-production
JWT_EXPIRES_IN=7d

# AI Configuration
OPENAI_API_KEY=your-openai-api-key-here
COHERE_API_KEY=your-cohere-api-key-here

# Email Configuration
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=

# File Storage
UPLOAD_DIR=/opt/docassembler/shared/uploads
MAX_FILE_SIZE=50MB

# Vector Database
CHROMADB_HOST=localhost
CHROMADB_PORT=8000

# Application URLs
FRONTEND_URL=https://app.yourdomain.com
API_URL=https://api.yourdomain.com
EOF

# Upload application to server
print_status "Uploading application to server..."
rsync -avz --delete \
    --exclude node_modules \
    --exclude .git \
    --exclude '*.log' \
    "$TEMP_DEPLOY_DIR/" \
    "$DEPLOY_USER@$SERVER_IP:$RELEASE_DIR/"

# Install dependencies on server
print_status "Installing dependencies on server..."
ssh "$DEPLOY_USER@$SERVER_IP" "
    cd $RELEASE_DIR
    npm ci --production
    
    # Link shared directories
    rm -rf logs data uploads config
    ln -sf $DEPLOY_PATH/shared/logs logs
    ln -sf $DEPLOY_PATH/shared/data data
    ln -sf $DEPLOY_PATH/shared/uploads uploads
    ln -sf $DEPLOY_PATH/shared/config config
    
    # Copy environment file if it doesn't exist
    if [ ! -f $DEPLOY_PATH/shared/config/.env ]; then
        cp .env.example $DEPLOY_PATH/shared/config/.env
        echo 'Environment file created at $DEPLOY_PATH/shared/config/.env'
        echo 'Please edit this file with your actual configuration'
    fi
    
    ln -sf $DEPLOY_PATH/shared/config/.env .env
"

# Create systemd service file
print_status "Creating systemd service..."
ssh "$DEPLOY_USER@$SERVER_IP" "
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << 'EOF'
[Unit]
Description=DocAssembler Application
Documentation=https://github.com/cloudcurio/doc_assembler_web
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=$DEPLOY_USER
WorkingDirectory=$DEPLOY_PATH/current
Environment=NODE_ENV=$ENVIRONMENT
ExecStart=/usr/bin/node server.js
Restart=on-failure
RestartSec=10
KillMode=process
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
"

# Stop current service if running
print_status "Stopping current service..."
ssh "$DEPLOY_USER@$SERVER_IP" "
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        sudo systemctl stop $SERVICE_NAME
        echo 'Service stopped'
    else
        echo 'Service was not running'
    fi
"

# Switch to new release
print_status "Switching to new release..."
ssh "$DEPLOY_USER@$SERVER_IP" "
    # Update current symlink
    rm -f $DEPLOY_PATH/current
    ln -sf $RELEASE_DIR $DEPLOY_PATH/current
    
    echo 'Symlink updated to new release'
"

# Start service
print_status "Starting application service..."
ssh "$DEPLOY_USER@$SERVER_IP" "
    sudo systemctl enable $SERVICE_NAME
    sudo systemctl start $SERVICE_NAME
    
    # Wait for service to start
    sleep 5
    
    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        echo 'Service started successfully'
    else
        echo 'Service failed to start'
        sudo systemctl status $SERVICE_NAME
        exit 1
    fi
"

# Health check
print_status "Performing health check..."
sleep 10

# Check if application is responding
if ssh "$DEPLOY_USER@$SERVER_IP" "curl -f http://localhost:3000/health >/dev/null 2>&1"; then
    print_status "Health check passed"
else
    print_warning "Health check failed"
    
    if [ "$ROLLBACK_ENABLED" = true ]; then
        print_status "Rolling back to previous release..."
        ssh "$DEPLOY_USER@$SERVER_IP" "
            if [ -d $DEPLOY_PATH/backup/backup_$DEPLOY_TIMESTAMP ]; then
                sudo systemctl stop $SERVICE_NAME
                rm -f $DEPLOY_PATH/current
                ln -sf $DEPLOY_PATH/backup/backup_$DEPLOY_TIMESTAMP $DEPLOY_PATH/current
                sudo systemctl start $SERVICE_NAME
                echo 'Rollback completed'
            else
                echo 'No backup found for rollback'
            fi
        "
    fi
    
    print_error "Deployment may have issues. Please check logs."
    exit 1
fi

# Cleanup old releases (keep last 5)
print_status "Cleaning up old releases..."
ssh "$DEPLOY_USER@$SERVER_IP" "
    cd $DEPLOY_PATH/releases
    ls -1t | tail -n +6 | xargs -r rm -rf
    echo 'Old releases cleaned up'
"

print_status "Deployment completed successfully! 🎉"
print_info "Application URL: http://$SERVER_IP:3000"
print_info "Service status: sudo systemctl status $SERVICE_NAME"
print_info "Logs: sudo journalctl -u $SERVICE_NAME -f"

echo ""
echo "Next steps:"
echo "1. Configure your environment file: $DEPLOY_PATH/shared/config/.env"
echo "2. Set up reverse proxy (Nginx) for production"
echo "3. Configure SSL certificates"
echo "4. Set up monitoring and alerting"
echo "5. Test all application features"

