#!/bin/bash

# DocAssembler Database Restore Script
# Restores PostgreSQL and Redis databases from backup files

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

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
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[RESTORE]${NC} $1"
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
    echo "Usage: $0 [OPTIONS] BACKUP_DIR"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -p, --postgresql        Restore PostgreSQL only"
    echo "  -r, --redis             Restore Redis only"
    echo "  -c, --chromadb          Restore ChromaDB only"
    echo "  -a, --app-data          Restore application data only"
    echo "  -f, --force             Skip confirmation prompts"
    echo ""
    echo "Arguments:"
    echo "  BACKUP_DIR              Path to backup directory"
    echo ""
    echo "Examples:"
    echo "  $0 /path/to/backup/2025-06-24"
    echo "  $0 --postgresql --force /path/to/backup/2025-06-24"
    echo "  $0 --redis /path/to/backup/2025-06-24"
}

# Parse command line arguments
RESTORE_POSTGRESQL=false
RESTORE_REDIS=false
RESTORE_CHROMADB=false
RESTORE_APP_DATA=false
RESTORE_ALL=true
FORCE=false
BACKUP_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -p|--postgresql)
            RESTORE_POSTGRESQL=true
            RESTORE_ALL=false
            shift
            ;;
        -r|--redis)
            RESTORE_REDIS=true
            RESTORE_ALL=false
            shift
            ;;
        -c|--chromadb)
            RESTORE_CHROMADB=true
            RESTORE_ALL=false
            shift
            ;;
        -a|--app-data)
            RESTORE_APP_DATA=true
            RESTORE_ALL=false
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        *)
            if [ -z "$BACKUP_DIR" ]; then
                BACKUP_DIR="$1"
            else
                print_error "Unknown option: $1"
                usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate backup directory
if [ -z "$BACKUP_DIR" ]; then
    print_error "Backup directory not specified"
    usage
    exit 1
fi

if [ ! -d "$BACKUP_DIR" ]; then
    print_error "Backup directory does not exist: $BACKUP_DIR"
    exit 1
fi

# Set restore flags if restoring all
if [ "$RESTORE_ALL" = true ]; then
    RESTORE_POSTGRESQL=true
    RESTORE_REDIS=true
    RESTORE_CHROMADB=true
    RESTORE_APP_DATA=true
fi

print_status "Starting database restore process..."
print_status "Backup directory: $BACKUP_DIR"

# Show backup manifest if available
if [ -f "$BACKUP_DIR/backup_manifest.txt" ]; then
    print_info "Backup manifest:"
    cat "$BACKUP_DIR/backup_manifest.txt"
    echo ""
fi

# Confirmation prompt
if [ "$FORCE" != true ]; then
    echo "⚠️  WARNING: This operation will overwrite existing data!"
    echo ""
    echo "Restore operations planned:"
    [ "$RESTORE_POSTGRESQL" = true ] && echo "  ✓ PostgreSQL database"
    [ "$RESTORE_REDIS" = true ] && echo "  ✓ Redis data"
    [ "$RESTORE_CHROMADB" = true ] && echo "  ✓ ChromaDB vector data"
    [ "$RESTORE_APP_DATA" = true ] && echo "  ✓ Application data"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_warning "Restore cancelled by user"
        exit 0
    fi
fi

# Find backup files
POSTGRESQL_DUMP=$(find "$BACKUP_DIR" -name "postgresql_*.dump" | head -1)
POSTGRESQL_SQL=$(find "$BACKUP_DIR" -name "postgresql_*.sql.gz" | head -1)
REDIS_DUMP=$(find "$BACKUP_DIR" -name "redis_*.rdb.gz" | head -1)
CHROMADB_ARCHIVE=$(find "$BACKUP_DIR" -name "chromadb_*.tar.gz" | head -1)
APP_DATA_ARCHIVE=$(find "$BACKUP_DIR" -name "app_data_*.tar.gz" | head -1)

# PostgreSQL Restore
if [ "$RESTORE_POSTGRESQL" = true ]; then
    print_status "Restoring PostgreSQL database..."
    
    if [ -n "$POSTGRESQL_DUMP" ] && [ -f "$POSTGRESQL_DUMP" ]; then
        print_info "Using PostgreSQL dump: $POSTGRESQL_DUMP"
        
        # Drop existing database connections
        PGPASSWORD="$DB_PASSWORD" psql \
            --host="$DB_HOST" \
            --port="$DB_PORT" \
            --username="$DB_USER" \
            --dbname="postgres" \
            --command="SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();" || true
        
        # Restore from custom dump
        PGPASSWORD="$DB_PASSWORD" pg_restore \
            --host="$DB_HOST" \
            --port="$DB_PORT" \
            --username="$DB_USER" \
            --dbname="postgres" \
            --clean \
            --if-exists \
            --create \
            --verbose \
            "$POSTGRESQL_DUMP"
        
        print_status "PostgreSQL restore completed"
        
    elif [ -n "$POSTGRESQL_SQL" ] && [ -f "$POSTGRESQL_SQL" ]; then
        print_info "Using PostgreSQL SQL backup: $POSTGRESQL_SQL"
        
        # Decompress and restore SQL backup
        zcat "$POSTGRESQL_SQL" | PGPASSWORD="$DB_PASSWORD" psql \
            --host="$DB_HOST" \
            --port="$DB_PORT" \
            --username="$DB_USER" \
            --dbname="postgres"
        
        print_status "PostgreSQL restore completed"
    else
        print_warning "No PostgreSQL backup found in $BACKUP_DIR"
    fi
fi

# Redis Restore
if [ "$RESTORE_REDIS" = true ]; then
    print_status "Restoring Redis data..."
    
    if [ -n "$REDIS_DUMP" ] && [ -f "$REDIS_DUMP" ]; then
        print_info "Using Redis dump: $REDIS_DUMP"
        
        # Stop Redis service temporarily
        if systemctl is-active --quiet redis; then
            print_info "Stopping Redis service..."
            sudo systemctl stop redis
            REDIS_WAS_RUNNING=true
        else
            REDIS_WAS_RUNNING=false
        fi
        
        # Find Redis data directory
        REDIS_DATA_DIR="/var/lib/redis"
        if [ ! -d "$REDIS_DATA_DIR" ]; then
            REDIS_DATA_DIR="/opt/redis/data"
        fi
        
        if [ -d "$REDIS_DATA_DIR" ]; then
            # Backup current dump.rdb
            if [ -f "$REDIS_DATA_DIR/dump.rdb" ]; then
                sudo mv "$REDIS_DATA_DIR/dump.rdb" "$REDIS_DATA_DIR/dump.rdb.backup.$(date +%s)"
            fi
            
            # Restore Redis dump
            zcat "$REDIS_DUMP" | sudo tee "$REDIS_DATA_DIR/dump.rdb" > /dev/null
            sudo chown redis:redis "$REDIS_DATA_DIR/dump.rdb" 2>/dev/null || true
            
            # Restart Redis if it was running
            if [ "$REDIS_WAS_RUNNING" = true ]; then
                print_info "Starting Redis service..."
                sudo systemctl start redis
            fi
            
            print_status "Redis restore completed"
        else
            print_warning "Redis data directory not found"
        fi
    else
        print_warning "No Redis backup found in $BACKUP_DIR"
    fi
fi

# ChromaDB Restore
if [ "$RESTORE_CHROMADB" = true ]; then
    print_status "Restoring ChromaDB data..."
    
    if [ -n "$CHROMADB_ARCHIVE" ] && [ -f "$CHROMADB_ARCHIVE" ]; then
        print_info "Using ChromaDB archive: $CHROMADB_ARCHIVE"
        
        CHROMADB_PATH="${CHROMADB_PATH:-$PROJECT_ROOT/data/chromadb}"
        
        # Backup existing ChromaDB data
        if [ -d "$CHROMADB_PATH" ]; then
            mv "$CHROMADB_PATH" "${CHROMADB_PATH}.backup.$(date +%s)"
        fi
        
        # Create parent directory
        mkdir -p "$(dirname "$CHROMADB_PATH")"
        
        # Extract ChromaDB data
        tar -xzf "$CHROMADB_ARCHIVE" -C "$(dirname "$CHROMADB_PATH")"
        
        print_status "ChromaDB restore completed"
    else
        print_warning "No ChromaDB backup found in $BACKUP_DIR"
    fi
fi

# Application Data Restore
if [ "$RESTORE_APP_DATA" = true ]; then
    print_status "Restoring application data..."
    
    if [ -n "$APP_DATA_ARCHIVE" ] && [ -f "$APP_DATA_ARCHIVE" ]; then
        print_info "Using app data archive: $APP_DATA_ARCHIVE"
        
        APP_DATA_DIR="${APP_DATA_DIR:-$PROJECT_ROOT/data/uploads}"
        
        # Backup existing app data
        if [ -d "$APP_DATA_DIR" ]; then
            mv "$APP_DATA_DIR" "${APP_DATA_DIR}.backup.$(date +%s)"
        fi
        
        # Create parent directory
        mkdir -p "$(dirname "$APP_DATA_DIR")"
        
        # Extract application data
        tar -xzf "$APP_DATA_ARCHIVE" -C "$(dirname "$APP_DATA_DIR")"
        
        print_status "Application data restore completed"
    else
        print_warning "No application data backup found in $BACKUP_DIR"
    fi
fi

print_status "Database restore process completed!"
print_status "Please verify that all services are working correctly."

# Suggest verification steps
echo ""
echo "Verification steps:"
echo "1. Check PostgreSQL connection: psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
echo "2. Check Redis connection: redis-cli -h $REDIS_HOST -p $REDIS_PORT ping"
echo "3. Test application functionality"
echo "4. Check logs for any errors"

