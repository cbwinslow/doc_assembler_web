#!/bin/bash
set -e

# Function to handle cleanup and graceful shutdown
cleanup() {
    echo "Received shutdown signal - gracefully terminating..."
    
    # Send SIGTERM to the main process
    if [ ! -z "$child" ]; then
        kill -TERM "$child" 2>/dev/null
        # Wait for main process to terminate
        wait "$child"
    fi
    
    echo "Application terminated"
    exit 0
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Trap SIGTERM and SIGINT signals
trap cleanup SIGTERM SIGINT

# Initialize data directories if they don't exist
echo "Initializing data directories..."
mkdir -p \
    /app/data/assets \
    /app/data/cache \
    /app/data/playwright \
    /app/logs

# Set correct permissions
chown -R mcp:mcp \
    /app/data \
    /app/logs

# Wait for required services
echo "Waiting for PostgreSQL..."
./scripts/wait-for-it.sh "${POSTGRES_HOST:-postgres}:${POSTGRES_PORT:-5432}" -t 60

echo "Waiting for Redis..."
./scripts/wait-for-it.sh "${REDIS_HOST:-redis}:${REDIS_PORT:-6379}" -t 60

# Install/Update Playwright if needed
if ! command_exists playwright; then
    echo "Installing Playwright..."
    npm install -g playwright@1.40.0
    playwright install chromium
    playwright install-deps chromium
fi

# Run database migrations
echo "Running database migrations..."
poetry run alembic upgrade head

# Start the application
echo "Starting MCP server..."
poetry run uvicorn \
    mcp_server.api.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers "${WORKERS:-4}" \
    --limit-max-requests "${MAX_REQUESTS:-1000}" \
    --limit-max-requests-jitter "${MAX_REQUESTS_JITTER:-50}" \
    --timeout-keep-alive "${TIMEOUT:-120}" \
    --graceful-timeout "${GRACEFUL_TIMEOUT:-30}" \
    --log-level "${LOG_LEVEL:-INFO}" \
    --proxy-headers \
    --forwarded-allow-ips '*' &

# Store child PID
child=$!

# Log startup completion
echo "MCP server started with PID $child"

# Wait for the process to finish
wait "$child"

