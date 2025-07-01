# Stage 1: Build dependencies
FROM python:3.13-slim as builder

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.7.1
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    poetry config virtualenvs.create false

# Set working directory
WORKDIR /build

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root --no-dev

# Stage 2: Production image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    WORKERS=4 \
    MAX_REQUESTS=1000 \
    MAX_REQUESTS_JITTER=50 \
    TIMEOUT=120 \
    GRACEFUL_TIMEOUT=30 \
    LOG_LEVEL=INFO \
    PATH="/home/mcp/.local/bin:$PATH" \
    NODE_VERSION=20.x \
    DEBIAN_FRONTEND=noninteractive

# Create non-root user
RUN useradd -m -s /bin/bash mcp && \
    mkdir -p /app /app/data /app/logs /app/assets && \
    chown -R mcp:mcp /app

# Install system dependencies and Node.js
RUN apt-get update && \
    apt-get install -y \
    curl \
    postgresql-client \
    redis-tools \
    gnupg \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION} | bash - \
    && apt-get install -y \
    nodejs \
    && npm install -g npm@latest \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Install Poetry
ENV POETRY_VERSION=1.7.1
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    poetry config virtualenvs.create false

# Copy application code
COPY --chown=mcp:mcp . .

# Install the package
RUN poetry install --no-dev

# Install Playwright and browsers
RUN npm install -g playwright@1.40.0 && \
    npx playwright install chromium && \
    npx playwright install-deps chromium && \
    chown -R mcp:mcp /ms-playwright

# Create data directories with correct permissions
RUN mkdir -p \
    /app/data/assets \
    /app/data/cache \
    /app/data/playwright \
    /app/logs && \
    chown -R mcp:mcp /app/data /app/logs

# Copy scripts
COPY --chown=mcp:mcp scripts/wait-for-it.sh /app/scripts/wait-for-it.sh
COPY --chown=mcp:mcp scripts/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/scripts/wait-for-it.sh /app/entrypoint.sh

# Switch to non-root user
USER mcp

# Set environment variables for Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/app/data/playwright

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Security settings
# Note: These must be set in docker-compose.yml or docker run command
# --cap-drop=ALL
# --security-opt=no-new-privileges:true
# --cpus=2
# --memory=4g
# --memory-swap=4g

# Set resource limits
ENV GOMAXPROCS=2
ENV NODE_OPTIONS="--max-old-space-size=2048"

# Expose port
EXPOSE ${PORT}

# Use entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]

# Stage 1: Build dependencies
FROM python:3.13-slim as builder

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.7.1
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    poetry config virtualenvs.create false

# Set working directory
WORKDIR /build

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root --no-dev

# Stage 2: Production image
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    WORKERS=4 \
    MAX_REQUESTS=1000 \
    MAX_REQUESTS_JITTER=50 \
    TIMEOUT=120 \
    GRACEFUL_TIMEOUT=30 \
    LOG_LEVEL=INFO \
    PATH="/home/mcp/.local/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash mcp && \
    mkdir -p /app /app/data /app/logs /app/assets && \
    chown -R mcp:mcp /app

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Install Poetry (for potential runtime dependency management)
ENV POETRY_VERSION=1.7.1
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    poetry config virtualenvs.create false

# Copy application code
COPY --chown=mcp:mcp . .

# Install the package
RUN poetry install --no-dev

# Install Playwright browser
RUN playwright install chromium && \
    playwright install-deps chromium && \
    chown -R mcp:mcp /ms-playwright

# Create data directories with correct permissions
RUN mkdir -p \
    /app/data/assets \
    /app/data/cache \
    /app/data/playwright \
    /app/logs && \
    chown -R mcp:mcp /app/data /app/logs

# Switch to non-root user
USER mcp

# Set environment variables for Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/app/data/playwright

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Security: Drop capabilities and set resource limits
# Note: These must be set in docker-compose.yml or docker run command
# --cap-drop=ALL --security-opt=no-new-privileges:true
# --cpus=2 --memory=4g --memory-swap=4g

# Create startup script
COPY --chown=mcp:mcp <<EOF /app/start.sh
#!/bin/bash
set -e

# Wait for required services
./scripts/wait-for-it.sh ${POSTGRES_HOST}:${POSTGRES_PORT} -t 60
./scripts/wait-for-it.sh ${REDIS_HOST}:${REDIS_PORT} -t 60

# Run database migrations
poetry run alembic upgrade head

# Start the application
exec poetry run uvicorn \
    mcp_server.api.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers $WORKERS \
    --limit-max-requests $MAX_REQUESTS \
    --limit-max-requests-jitter $MAX_REQUESTS_JITTER \
    --timeout-keep-alive $TIMEOUT \
    --graceful-timeout $GRACEFUL_TIMEOUT \
    --log-level $LOG_LEVEL \
    --proxy-headers \
    --forwarded-allow-ips '*'
EOF

RUN chmod +x /app/start.sh

# Create wait-for-it script
COPY --chown=mcp:mcp <<EOF /app/scripts/wait-for-it.sh
#!/bin/bash
# wait-for-it.sh script content here
# (Add the standard wait-for-it.sh script content)
EOF

RUN chmod +x /app/scripts/wait-for-it.sh

# Run the application
CMD ["/app/start.sh"]

# Stage 1: Build dependencies
FROM python:3.13-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    poetry config virtualenvs.create false

# Set work directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-dev --no-root

# Stage 2: Production image
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/root/.local/bin:$PATH" \
    POETRY_VERSION=1.7.1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    poetry config virtualenvs.create false

# Set work directory
WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Install the package
RUN poetry install --no-dev

# Install Playwright browser
RUN playwright install chromium && \
    playwright install-deps chromium

# Create non-root user
RUN useradd -m mcp && \
    chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Expose port
EXPOSE 8000

# Create necessary directories with correct permissions
RUN mkdir -p /app/data/playwright && \
    mkdir -p /app/logs

# Set environment variables for Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/app/data/playwright

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "mcp_server.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers"]

