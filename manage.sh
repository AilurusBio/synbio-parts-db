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
    if [ ! -f "../data/parts.duckdb" ]; then
        error "Database file not found: ../data/parts.duckdb"
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
    
    # 优雅停止
    kill "$pid" 2>/dev/null
    sleep 3
    
    # 强制停止
    if ps -p "$pid" > /dev/null 2>&1; then
        warning "强制终止进程..."
        kill -9 "$pid" 2>/dev/null
        sleep 2
    fi
    
    rm -f "$PID_FILE"
    success "SynVectorDB 已停止"
}

# 重启服务
restart() {
    log "🔄 重启 SynVectorDB 服务..."
    stop
    sleep 2
    start
}

# 查看状态
status() {
    if is_running; then
        local pid=$(cat "$PID_FILE")
        success "SynVectorDB 正在运行 (PID: $pid)"
        log "📊 前端地址: http://localhost:8501"
        
        # 测试连接
        log "🔍 测试服务连接..."
        if curl -s http://localhost:8501 > /dev/null; then
            success "✅ 前端服务响应正常"
        else
            error "❌ 前端服务无响应"
        fi
    else
        warning "SynVectorDB 未运行"
    fi
}

# 查看日志
logs() {
    local lines=${1:-50}
    log "📝 显示最近 $lines 行日志..."
    echo "=== 应用日志 ==="
    tail -n "$lines" "$LOG_FILE" 2>/dev/null || echo "日志文件不存在"
    echo ""
    echo "=== 错误日志 ==="
    tail -n "$lines" "$ERROR_LOG" 2>/dev/null || echo "错误日志文件不存在"
}

# 实时日志
tail_logs() {
    log "📝 实时查看日志 (Ctrl+C 退出)..."
    tail -f "$LOG_FILE" "$ERROR_LOG" 2>/dev/null
}

# 测试服务
test() {
    log "🧪 测试 SynVectorDB 服务..."
    
    if ! is_running; then
        error "服务未运行，请先启动服务"
        return 1
    fi
    
    # 测试前端
    log "测试前端服务..."
    if curl -s http://localhost:8501 > /dev/null; then
        success "✅ 前端服务正常"
    else
        error "❌ 前端服务异常"
    fi
    
    # 测试数据库连接
    log "测试数据库连接..."
    cd "$APP_DIR"
    if python3 -c "
import duckdb
conn = duckdb.connect('../data/parts.duckdb')
count = conn.execute('SELECT COUNT(*) FROM parts').fetchone()[0]
print(f'数据库连接成功，共 {count} 个部件')
conn.close()
" 2>/dev/null; then
        success "✅ 数据库连接正常"
    else
        error "❌ 数据库连接异常"
    fi
}

# 清理日志
clean() {
    log "🧹 清理日志文件..."
    > "$LOG_FILE"
    > "$ERROR_LOG"
    success "日志文件已清理"
}

# 显示帮助
help() {
    echo "SynVectorDB 管理脚本"
    echo ""
    echo "用法: $0 {start|stop|restart|status|logs|tail|test|clean|help}"
    echo ""
    echo "命令:"
    echo "  start     启动服务"
    echo "  stop      停止服务"
    echo "  restart   重启服务"
    echo "  status    查看状态"
    echo "  logs [n]  查看最近n行日志 (默认50行)"
    echo "  tail      实时查看日志"
    echo "  test      测试服务"
    echo "  clean     清理日志"
    echo "  help      显示帮助"
    echo ""
    echo "服务信息:"
    echo "  前端地址: http://localhost:8501"
    echo "  日志文件: $LOG_FILE"
    echo "  错误日志: $ERROR_LOG"
    echo "  PID文件:  $PID_FILE"
}

# 主函数
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
