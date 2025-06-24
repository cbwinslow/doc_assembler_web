#!/bin/bash

# DocAssembler Performance Monitoring Script
# Monitors application performance, database health, and system resources

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Monitoring configuration
MONITOR_INTERVAL="${MONITOR_INTERVAL:-60}"
LOG_FILE="${LOG_FILE:-$PROJECT_ROOT/logs/monitor.log}"
ALERT_THRESHOLD_CPU="${ALERT_THRESHOLD_CPU:-80}"
ALERT_THRESHOLD_MEMORY="${ALERT_THRESHOLD_MEMORY:-85}"
ALERT_THRESHOLD_DISK="${ALERT_THRESHOLD_DISK:-90}"
ALERT_THRESHOLD_RESPONSE_TIME="${ALERT_THRESHOLD_RESPONSE_TIME:-2000}"

# Service configuration
APP_URL="${APP_URL:-http://localhost:3000}"
API_URL="${API_URL:-http://localhost:3000/api}"
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
CYAN='\033[0;36m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[MONITOR]${NC} $1"
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

print_metric() {
    echo -e "${CYAN}[METRIC]${NC} $1"
}

# Logging function
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Create log directory if it doesn't exist
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Write to log file
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    # Also print to console based on level
    case "$level" in
        "ERROR")
            print_error "$message"
            ;;
        "WARNING")
            print_warning "$message"
            ;;
        "INFO")
            print_info "$message"
            ;;
        "METRIC")
            print_metric "$message"
            ;;
        *)
            echo "$message"
            ;;
    esac
}

# System resource monitoring
check_system_resources() {
    print_status "Checking system resources..."
    
    # CPU Usage
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}' | sed 's/us,//')
    CPU_USAGE_INT=$(printf "%.0f" "$CPU_USAGE")
    
    if [ "$CPU_USAGE_INT" -gt "$ALERT_THRESHOLD_CPU" ]; then
        log_message "WARNING" "High CPU usage: ${CPU_USAGE}%"
    else
        log_message "METRIC" "CPU usage: ${CPU_USAGE}%"
    fi
    
    # Memory Usage
    MEMORY_INFO=$(free | grep Mem)
    MEMORY_TOTAL=$(echo $MEMORY_INFO | awk '{print $2}')
    MEMORY_USED=$(echo $MEMORY_INFO | awk '{print $3}')
    MEMORY_USAGE=$((MEMORY_USED * 100 / MEMORY_TOTAL))
    
    if [ "$MEMORY_USAGE" -gt "$ALERT_THRESHOLD_MEMORY" ]; then
        log_message "WARNING" "High memory usage: ${MEMORY_USAGE}%"
    else
        log_message "METRIC" "Memory usage: ${MEMORY_USAGE}%"
    fi
    
    # Disk Usage
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [ "$DISK_USAGE" -gt "$ALERT_THRESHOLD_DISK" ]; then
        log_message "WARNING" "High disk usage: ${DISK_USAGE}%"
    else
        log_message "METRIC" "Disk usage: ${DISK_USAGE}%"
    fi
    
    # Load Average
    LOAD_AVERAGE=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    log_message "METRIC" "Load average (1min): $LOAD_AVERAGE"
}

# Application health monitoring
check_application_health() {
    print_status "Checking application health..."
    
    # Health endpoint check
    if command -v curl &> /dev/null; then
        local start_time=$(date +%s%3N)
        local http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$APP_URL/health" 2>/dev/null || echo "000")
        local end_time=$(date +%s%3N)
        local response_time=$((end_time - start_time))
        
        if [ "$http_code" = "200" ]; then
            if [ "$response_time" -gt "$ALERT_THRESHOLD_RESPONSE_TIME" ]; then
                log_message "WARNING" "Slow application response: ${response_time}ms"
            else
                log_message "METRIC" "Application response time: ${response_time}ms"
            fi
        else
            log_message "ERROR" "Application health check failed (HTTP $http_code)"
        fi
    else
        log_message "WARNING" "curl not available for health checks"
    fi
    
    # Check if application process is running
    if pgrep -f "node.*server.js" > /dev/null; then
        log_message "METRIC" "Application process: Running"
    elif systemctl is-active --quiet docassembler; then
        log_message "METRIC" "Application service: Running"
    else
        log_message "ERROR" "Application process: Not running"
    fi
}

# Database monitoring
check_database_health() {
    print_status "Checking database health..."
    
    # PostgreSQL health
    if command -v psql &> /dev/null; then
        local pg_start=$(date +%s%3N)
        if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &> /dev/null; then
            local pg_end=$(date +%s%3N)
            local pg_response=$((pg_end - pg_start))
            log_message "METRIC" "PostgreSQL response time: ${pg_response}ms"
            
            # Get database size
            local db_size=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT pg_size_pretty(pg_database_size('$DB_NAME'));" 2>/dev/null | xargs || echo "Unknown")
            log_message "METRIC" "Database size: $db_size"
            
            # Get active connections
            local active_conns=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" 2>/dev/null | xargs || echo "Unknown")
            log_message "METRIC" "Active DB connections: $active_conns"
        else
            log_message "ERROR" "PostgreSQL connection failed"
        fi
    else
        log_message "WARNING" "psql not available for database checks"
    fi
    
    # Redis health
    if command -v redis-cli &> /dev/null; then
        local redis_start=$(date +%s%3N)
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping &> /dev/null; then
            local redis_end=$(date +%s%3N)
            local redis_response=$((redis_end - redis_start))
            log_message "METRIC" "Redis response time: ${redis_response}ms"
            
            # Get Redis memory usage
            local redis_memory=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" INFO memory | grep "used_memory_human" | cut -d: -f2 | tr -d '\r' || echo "Unknown")
            log_message "METRIC" "Redis memory usage: $redis_memory"
            
            # Get Redis connected clients
            local redis_clients=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" INFO clients | grep "connected_clients" | cut -d: -f2 | tr -d '\r' || echo "Unknown")
            log_message "METRIC" "Redis connected clients: $redis_clients"
        else
            log_message "ERROR" "Redis connection failed"
        fi
    else
        log_message "WARNING" "redis-cli not available for Redis checks"
    fi
}

# API endpoint monitoring
check_api_endpoints() {
    print_status "Checking API endpoints..."
    
    if command -v curl &> /dev/null; then
        # Common API endpoints to test
        local endpoints=(
            "$API_URL/health"
            "$API_URL/auth/status"
            "$API_URL/documents"
        )
        
        for endpoint in "${endpoints[@]}"; do
            local start_time=$(date +%s%3N)
            local http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$endpoint" 2>/dev/null || echo "000")
            local end_time=$(date +%s%3N)
            local response_time=$((end_time - start_time))
            
            local endpoint_name=$(echo "$endpoint" | sed "s|$API_URL||")
            
            if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 400 ]; then
                log_message "METRIC" "API $endpoint_name: ${response_time}ms (HTTP $http_code)"
            else
                log_message "WARNING" "API $endpoint_name: Failed (HTTP $http_code)"
            fi
        done
    fi
}

# Log file monitoring
check_log_files() {
    print_status "Checking log files..."
    
    # Application logs
    local app_log_patterns=(
        "/var/log/docassembler/*.log"
        "$PROJECT_ROOT/logs/*.log"
        "/opt/docassembler/shared/logs/*.log"
    )
    
    for pattern in "${app_log_patterns[@]}"; do
        for log_file in $pattern; do
            if [ -f "$log_file" ]; then
                # Check for recent errors
                local error_count=$(tail -n 100 "$log_file" | grep -i error | wc -l || echo "0")
                local warning_count=$(tail -n 100 "$log_file" | grep -i warning | wc -l || echo "0")
                
                if [ "$error_count" -gt 0 ]; then
                    log_message "WARNING" "Found $error_count errors in $(basename "$log_file") (last 100 lines)"
                fi
                
                if [ "$warning_count" -gt 5 ]; then
                    log_message "WARNING" "Found $warning_count warnings in $(basename "$log_file") (last 100 lines)"
                fi
                
                # Check log file size
                local log_size=$(du -h "$log_file" | cut -f1)
                log_message "METRIC" "Log file $(basename "$log_file"): $log_size"
            fi
        done
    done
}

# Generate monitoring report
generate_report() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo ""
    echo "===========================================" 
    echo "DocAssembler Monitoring Report"
    echo "Generated: $timestamp"
    echo "==========================================="
    
    echo ""
    echo "System Resources:"
    echo "  CPU Usage: ${CPU_USAGE}%"
    echo "  Memory Usage: ${MEMORY_USAGE}%"
    echo "  Disk Usage: ${DISK_USAGE}%"
    echo "  Load Average: $LOAD_AVERAGE"
    
    echo ""
    echo "Application Status:"
    echo "  Health Check: $([ "$http_code" = "200" ] && echo "✓ Healthy" || echo "✗ Unhealthy")"
    echo "  Response Time: ${response_time}ms"
    
    echo ""
    echo "Recent Log Summary:"
    echo "  Monitor Log: $LOG_FILE"
    echo "  Last check: $timestamp"
    
    echo ""
    echo "Recommendations:"
    if [ "$CPU_USAGE_INT" -gt "$ALERT_THRESHOLD_CPU" ]; then
        echo "  - High CPU usage detected - consider scaling"
    fi
    if [ "$MEMORY_USAGE" -gt "$ALERT_THRESHOLD_MEMORY" ]; then
        echo "  - High memory usage detected - check for memory leaks"
    fi
    if [ "$DISK_USAGE" -gt "$ALERT_THRESHOLD_DISK" ]; then
        echo "  - High disk usage - clean up logs or expand storage"
    fi
    if [ "$response_time" -gt "$ALERT_THRESHOLD_RESPONSE_TIME" ]; then
        echo "  - Slow response times - investigate performance bottlenecks"
    fi
    
    echo "==========================================="
}

# Main monitoring function
run_monitoring() {
    log_message "INFO" "Starting monitoring cycle"
    
    check_system_resources
    check_application_health
    check_database_health
    check_api_endpoints
    check_log_files
    
    log_message "INFO" "Monitoring cycle completed"
}

# Usage function
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -i, --interval SECONDS  Monitoring interval (default: 60)"
    echo "  -o, --once              Run once and exit"
    echo "  -r, --report            Generate and display report"
    echo "  -l, --log-file FILE     Log file path (default: $LOG_FILE)"
    echo ""
    echo "Examples:"
    echo "  $0                      # Run continuous monitoring"
    echo "  $0 --once              # Run single check"
    echo "  $0 --interval 30       # Monitor every 30 seconds"
    echo "  $0 --report            # Generate report"
}

# Parse command line arguments
RUN_ONCE=false
SHOW_REPORT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -i|--interval)
            MONITOR_INTERVAL="$2"
            shift 2
            ;;
        -o|--once)
            RUN_ONCE=true
            shift
            ;;
        -r|--report)
            SHOW_REPORT=true
            shift
            ;;
        -l|--log-file)
            LOG_FILE="$2"
            shift 2
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Main execution
print_status "DocAssembler Monitoring Script"
print_info "Log file: $LOG_FILE"
print_info "Monitoring interval: ${MONITOR_INTERVAL}s"

if [ "$RUN_ONCE" = true ]; then
    run_monitoring
    if [ "$SHOW_REPORT" = true ]; then
        generate_report
    fi
elif [ "$SHOW_REPORT" = true ]; then
    run_monitoring
    generate_report
else
    print_status "Starting continuous monitoring (Press Ctrl+C to stop)"
    
    # Set up signal handlers for graceful shutdown
    trap 'log_message "INFO" "Monitoring stopped by user"; exit 0' INT TERM
    
    while true; do
        run_monitoring
        sleep "$MONITOR_INTERVAL"
    done
fi

