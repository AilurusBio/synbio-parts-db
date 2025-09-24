#!/bin/bash

# SynVectorDB githubshare - Enhanced Version Management Script
# 管理增强版本的启动、停止和测试

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STREAMLIT_DIR="$SCRIPT_DIR/streamlit_app"
PID_FILE="$SCRIPT_DIR/.enhanced_app.pid"
LOG_FILE="$SCRIPT_DIR/enhanced_app.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARN:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# 检查依赖
check_dependencies() {
    log "检查增强版依赖..."
    
    python3 -c "import streamlit, duckdb, sentence_transformers, faiss" 2>/dev/null
    if [ $? -ne 0 ]; then
        error "缺少必要依赖，请运行: pip install -r requirements_enhanced.txt"
        return 1
    fi
    
    # 检查数据库
    if [ ! -f "$SCRIPT_DIR/data/parts.duckdb" ]; then
        error "DuckDB数据库文件不存在: $SCRIPT_DIR/data/parts.duckdb"
        return 1
    fi
    
    # 检查模型
    if [ ! -d "$STREAMLIT_DIR/models/models--sentence-transformers--all-MiniLM-L6-v2" ]; then
        error "向量模型不存在: $STREAMLIT_DIR/models/"
        return 1
    fi
    
    log "所有依赖检查通过"
    return 0
}

# 启动服务
start() {
    log "启动 SynVectorDB githubshare Enhanced..."
    
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            warn "服务已在运行 (PID: $pid)"
            return 1
        else
            rm -f "$PID_FILE"
        fi
    fi
    
    check_dependencies || return 1
    
    cd "$STREAMLIT_DIR"
    
    info "启动增强版应用..."
    info "首次启动可能需要几分钟构建向量索引"
    
    nohup python3 -m streamlit run Home_enhanced.py \
        --server.port 8501 \
        --server.address localhost \
        --server.headless true \
        --browser.gatherUsageStats false \
        > "$LOG_FILE" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_FILE"
    
    sleep 3
    
    if kill -0 "$pid" 2>/dev/null; then
        log "✅ SynVectorDB Enhanced 启动成功 (PID: $pid)"
        info "📊 前端地址: http://localhost:8501"
        info "🔍 功能: DuckDB + 本地向量搜索"
        return 0
    else
        error "启动失败"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 停止服务
stop() {
    log "停止 SynVectorDB githubshare Enhanced..."
    
    if [ ! -f "$PID_FILE" ]; then
        warn "服务未运行"
        return 1
    fi
    
    local pid=$(cat "$PID_FILE")
    
    if kill -0 "$pid" 2>/dev/null; then
        kill "$pid"
        sleep 2
        
        if kill -0 "$pid" 2>/dev/null; then
            warn "强制终止进程..."
            kill -9 "$pid"
        fi
        
        rm -f "$PID_FILE"
        log "✅ 服务已停止"
    else
        warn "进程不存在，清理PID文件"
        rm -f "$PID_FILE"
    fi
}

# 重启服务
restart() {
    log "重启 SynVectorDB githubshare Enhanced..."
    stop
    sleep 2
    start
}

# 查看状态
status() {
    log "检查 SynVectorDB Enhanced 状态..."
    
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log "✅ SynVectorDB Enhanced 正在运行 (PID: $pid)"
            info "📊 前端地址: http://localhost:8501"
            
            # 测试服务连接
            if command -v curl >/dev/null 2>&1; then
                info "🔍 测试服务连接..."
                if curl -s "http://localhost:8501" >/dev/null; then
                    log "✅ 前端服务响应正常"
                else
                    warn "前端服务无响应"
                fi
            fi
            
            return 0
        else
            error "PID文件存在但进程不运行"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        warn "服务未运行"
        return 1
    fi
}

# 查看日志
logs() {
    if [ -f "$LOG_FILE" ]; then
        log "显示应用日志 (最后50行):"
        tail -n 50 "$LOG_FILE"
    else
        warn "日志文件不存在"
    fi
}

# 测试功能
test() {
    log "测试增强版功能..."
    
    cd "$SCRIPT_DIR"
    python3 test_enhanced_features.py
    
    if [ $? -eq 0 ]; then
        log "✅ 功能测试通过"
    else
        error "功能测试失败"
        return 1
    fi
}

# 清理
clean() {
    log "清理增强版应用..."
    
    stop
    
    if [ -f "$LOG_FILE" ]; then
        rm -f "$LOG_FILE"
        info "已删除日志文件"
    fi
    
    # 清理Python缓存
    find "$SCRIPT_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
    find "$SCRIPT_DIR" -name "*.pyc" -delete 2>/dev/null
    
    log "✅ 清理完成"
}

# 显示帮助
help() {
    echo "SynVectorDB githubshare - Enhanced Version Management"
    echo "使用方法: $0 {start|stop|restart|status|logs|test|clean|help}"
    echo ""
    echo "命令说明:"
    echo "  start   - 启动增强版应用 (DuckDB + 本地向量搜索)"
    echo "  stop    - 停止应用"
    echo "  restart - 重启应用"
    echo "  status  - 查看运行状态"
    echo "  logs    - 查看应用日志"
    echo "  test    - 运行功能测试"
    echo "  clean   - 清理应用和日志"
    echo "  help    - 显示此帮助"
    echo ""
    echo "增强功能:"
    echo "  ✅ DuckDB 数据库集成"
    echo "  ✅ 本地向量搜索 (sentence-transformers)"
    echo "  ✅ FAISS 加速相似度搜索"
    echo "  ✅ 实时向量计算"
    echo "  ✅ 增强统计分析"
}

# 主逻辑
case "$1" in
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
        logs
        ;;
    test)
        test
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        help
        ;;
    *)
        error "未知命令: $1"
        help
        exit 1
        ;;
esac

exit $?
