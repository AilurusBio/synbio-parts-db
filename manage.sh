#!/bin/bash
# SynVectorDB Management Script - Start, Stop, Log Management

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR/streamlit_app"
PID_FILE="$SCRIPT_DIR/.synvectordb.pid"
LOG_FILE="$SCRIPT_DIR/logs/synvectordb.log"
ERROR_LOG="$SCRIPT_DIR/logs/error.log"

# Create log directory
mkdir -p "$SCRIPT_DIR/logs"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1" >> "$ERROR_LOG"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $1" >> "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING] $1" >> "$LOG_FILE"
}

# Check if process is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Start service
start() {
    log "🚀 Starting SynVectorDB service..."
    
    if is_running; then
        warning "Service already running (PID: $(cat "$PID_FILE"))"
        return 1
    fi
    
    # Check dependencies
    log "📦 Checking dependencies..."
    cd "$APP_DIR"
    
    if ! python3 -c "import streamlit, duckdb, pandas, plotly" 2>/dev/null; then
        log "Installing missing dependencies..."
        pip3 install -r requirements.txt >> "$LOG_FILE" 2>> "$ERROR_LOG"
    fi
    
    # Check data files
    if [ ! -f "$SCRIPT_DIR/data/parts.duckdb" ]; then
        error "Database file not found: $SCRIPT_DIR/data/parts.duckdb"
        return 1
    fi
    
    # Start Streamlit application
    log "🌐 Starting Streamlit application (port: 8501)..."
    nohup streamlit run Home.py --server.port 8501 --server.address 0.0.0.0 --server.headless true >> "$LOG_FILE" 2>> "$ERROR_LOG" &
    local pid=$!
    echo $pid > "$PID_FILE"
    
    # Wait for startup
    sleep 5
    
    if is_running; then
        success "SynVectorDB started successfully!"
        log "📊 Frontend URL: http://localhost:8501"
        log "📝 Log file: $LOG_FILE"
        log "❌ Error log: $ERROR_LOG"
        log "🔍 Use '$0 status' to check status"
        log "⏹️  Use '$0 stop' to stop service"
    else
        error "Startup failed, please check log: $ERROR_LOG"
        return 1
    fi
}

# Stop service
stop() {
    log "⏹️  Stopping SynVectorDB service..."
    
    if ! is_running; then
        warning "Service not running"
        return 1
    fi
    
    local pid=$(cat "$PID_FILE")
    log "Terminating process PID: $pid"
    
    # Graceful stop
    kill "$pid" 2>/dev/null
    sleep 3
    
    # Force stop
    if ps -p "$pid" > /dev/null 2>&1; then
        warning "Force terminating process..."
        kill -9 "$pid" 2>/dev/null
        sleep 2
    fi
    
    rm -f "$PID_FILE"
    success "SynVectorDB stopped"
}

# Restart service
restart() {
    log "🔄 Restarting SynVectorDB service..."
    stop
    sleep 2
    start
}

# Check status
status() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        success "SynVectorDB is running (PID: $pid)"
        log "📊 Frontend URL: http://localhost:8501"
        
        # Test connection
        log "🔍 Testing service connection..."
        if curl -s http://localhost:8501 > /dev/null; then
            success "✅ Frontend service responding normally"
        else
            error "❌ Frontend service not responding"
        fi
    else
        warning "SynVectorDB not running"
    fi
}

# View logs
logs() {
    local lines=${1:-50}
    log "📝 Showing last $lines lines of logs..."
    echo "=== Application Logs ==="
    tail -n "$lines" "$LOG_FILE" 2>/dev/null || echo "Log file not found"
    echo ""
    echo "=== Error Logs ==="
    tail -n "$lines" "$ERROR_LOG" 2>/dev/null || echo "Error log file not found"
}

# Real-time logs
tail_logs() {
    log "📝 Real-time log viewing - Ctrl+C to exit..."
    tail -f "$LOG_FILE" "$ERROR_LOG" 2>/dev/null
}

# Test service
test() {
    log "🧪 Testing SynVectorDB service..."
    
    if ! is_running; then
        error "Service not running, please start service first"
        return 1
    fi
    
    # Test frontend
    log "Testing frontend service..."
    if curl -s http://localhost:8501 > /dev/null; then
        success "✅ Frontend service normal"
    else
        error "❌ Frontend service abnormal"
    fi
    
    # Test database connection
    log "Testing database connection..."
    cd "$APP_DIR"
    if python3 -c "
import duckdb
conn = duckdb.connect('$SCRIPT_DIR/data/parts.duckdb')
count = conn.execute('SELECT COUNT(*) FROM parts').fetchone()[0]
print(f'Database connected successfully, {count} parts found')
conn.close()
" 2>/dev/null; then
        success "✅ Database connection normal"
    else
        error "❌ Database connection abnormal"
    fi
}

# Clean logs
clean() {
    log "🧹 Cleaning log files..."
    > "$LOG_FILE"
    > "$ERROR_LOG"
    success "Log files cleaned"
}

# Show help
help() {
    echo "SynVectorDB Management Script"
    echo ""
    echo "Usage: $0 {start|stop|restart|status|logs|tail|test|clean|help}"
    echo ""
    echo "Commands:"
    echo "  start     Start service"
    echo "  stop      Stop service"
    echo "  restart   Restart service"
    echo "  status    Check status"
    echo "  logs [n]  View last n lines of logs (default 50)"
    echo "  tail      Real-time log viewing"
    echo "  test      Test service"
    echo "  clean     Clean log files"
    echo "  help      Show help"
    echo ""
    echo "Service Info:"
    echo "  Frontend URL: http://localhost:8501"
    echo "  Log file: $LOG_FILE"
    echo "  Error log: $ERROR_LOG"
    echo "  PID file:  $PID_FILE"
}

# Main function
case "${1:-help}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs "${2:-50}"
        ;;
    tail)
        tail_logs
        ;;
    test)
        test
        ;;
    clean)
        clean
        ;;
    help|*)
        help
        ;;
esac
