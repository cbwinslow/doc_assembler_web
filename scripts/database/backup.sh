#!/bin/bash

# DocAssembler Database Backup Script
# Backs up PostgreSQL and Redis databases with timestamp and compression

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_ROOT/backups/$(date +%Y-%m-%d)}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# Database configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-docassembler}"
DB_USER="${DB_USER:-docassembler_user}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[BACKUP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

print_status "Starting database backup process..."
print_status "Backup directory: $BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# PostgreSQL Backup
print_status "Backing up PostgreSQL database..."
if command -v pg_dump &> /dev/null; then
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --username="$DB_USER" \
        --dbname="$DB_NAME" \
        --no-password \
        --verbose \
        --clean \
        --if-exists \
        --create \
        --format=custom \
        --file="$BACKUP_DIR/postgresql_${TIMESTAMP}.dump"
    
    # Create a SQL version for easier inspection
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        --host="$DB_HOST" \
        --port="$DB_PORT" \
        --username="$DB_USER" \
        --dbname="$DB_NAME" \
        --no-password \
        --clean \
        --if-exists \
        --create \
        --file="$BACKUP_DIR/postgresql_${TIMESTAMP}.sql"
    
    # Compress SQL backup
    gzip "$BACKUP_DIR/postgresql_${TIMESTAMP}.sql"
    
    print_status "PostgreSQL backup completed"
else
    print_warning "pg_dump not found, skipping PostgreSQL backup"
fi

# Redis Backup
print_status "Backing up Redis data..."
if command -v redis-cli &> /dev/null; then
    # Create Redis backup using BGSAVE
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" BGSAVE
    
    # Wait for background save to complete
    while [ "$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" LASTSAVE)" -eq "$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" LASTSAVE)" ]; do
        sleep 1
    done
    
    # Copy the dump file
    REDIS_DATA_DIR=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" CONFIG GET dir | tail -1)
    if [ -f "${REDIS_DATA_DIR}/dump.rdb" ]; then
        cp "${REDIS_DATA_DIR}/dump.rdb" "$BACKUP_DIR/redis_${TIMESTAMP}.rdb"
        gzip "$BACKUP_DIR/redis_${TIMESTAMP}.rdb"
        print_status "Redis backup completed"
    else
        print_warning "Redis dump file not found at ${REDIS_DATA_DIR}/dump.rdb"
    fi
else
    print_warning "redis-cli not found, skipping Redis backup"
fi

# Vector Database Backup (ChromaDB)
print_status "Backing up ChromaDB data..."
CHROMADB_PATH="${CHROMADB_PATH:-$PROJECT_ROOT/data/chromadb}"
if [ -d "$CHROMADB_PATH" ]; then
    tar -czf "$BACKUP_DIR/chromadb_${TIMESTAMP}.tar.gz" -C "$(dirname "$CHROMADB_PATH")" "$(basename "$CHROMADB_PATH")"
    print_status "ChromaDB backup completed"
else
    print_warning "ChromaDB directory not found at $CHROMADB_PATH"
fi

# Application Data Backup
print_status "Backing up application data..."
APP_DATA_DIR="${APP_DATA_DIR:-$PROJECT_ROOT/data/uploads}"
if [ -d "$APP_DATA_DIR" ]; then
    tar -czf "$BACKUP_DIR/app_data_${TIMESTAMP}.tar.gz" -C "$(dirname "$APP_DATA_DIR")" "$(basename "$APP_DATA_DIR")"
    print_status "Application data backup completed"
else
    print_warning "Application data directory not found at $APP_DATA_DIR"
fi

# Create backup manifest
cat > "$BACKUP_DIR/backup_manifest.txt" << EOF
DocAssembler Database Backup
===========================
Timestamp: $(date)
Backup Directory: $BACKUP_DIR

Files included:
$(ls -la "$BACKUP_DIR")

Database Information:
- PostgreSQL Host: $DB_HOST:$DB_PORT
- Database Name: $DB_NAME
- Redis Host: $REDIS_HOST:$REDIS_PORT
- ChromaDB Path: $CHROMADB_PATH
- App Data Path: $APP_DATA_DIR

Backup completed successfully.
EOF

print_status "Backup manifest created"

# Cleanup old backups
print_status "Cleaning up old backups (keeping last $RETENTION_DAYS days)..."
find "$(dirname "$BACKUP_DIR")" -type d -name "*-*-*" -mtime +$RETENTION_DAYS -exec rm -rf {} + 2>/dev/null || true

# Calculate backup size
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
print_status "Backup completed successfully!"
print_status "Total backup size: $BACKUP_SIZE"
print_status "Backup location: $BACKUP_DIR"

echo ""
echo "Backup files created:"
ls -la "$BACKUP_DIR"

