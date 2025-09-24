#!/bin/bash

# SynVectorDB githubshare - Setup and Launch Script
# Automatically downloads data, installs dependencies, and starts the application

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"
LOGS_DIR="$SCRIPT_DIR/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARN:${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Check system requirements
check_requirements() {
    log "Checking system requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2)
    info "Python version: $python_version"
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        error "pip3 is required but not installed"
        exit 1
    fi
    
    log "✅ System requirements satisfied"
}

# Create necessary directories
setup_directories() {
    log "Setting up directories..."
    
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOGS_DIR"
    mkdir -p "$SCRIPT_DIR/streamlit_app/models"
    
    log "✅ Directories created"
}

# Install Python dependencies
install_dependencies() {
    log "Installing Python dependencies..."
    
    if [ -f "$SCRIPT_DIR/requirements_enhanced.txt" ]; then
        pip3 install -r "$SCRIPT_DIR/requirements_enhanced.txt"
        log "✅ Enhanced dependencies installed"
    elif [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        pip3 install -r "$SCRIPT_DIR/requirements.txt"
        log "✅ Basic dependencies installed"
    else
        warn "No requirements file found, installing basic dependencies"
        pip3 install streamlit pandas plotly duckdb sqlite3
    fi
}

# Download required data files
download_data() {
    log "Downloading required data files..."
    
    if [ -f "$SCRIPT_DIR/scripts/download_data.py" ]; then
        python3 "$SCRIPT_DIR/scripts/download_data.py"
        if [ $? -eq 0 ]; then
            log "✅ Data download completed"
        else
            error "Data download failed"
            exit 1
        fi
    else
        warn "Data download script not found, skipping..."
    fi
}

# Download AI models (if needed)
download_models() {
    log "Checking AI models..."
    
    model_dir="$SCRIPT_DIR/streamlit_app/models"
    if [ ! -d "$model_dir/models--sentence-transformers--all-MiniLM-L6-v2" ]; then
        info "AI models will be downloaded on first use"
        info "This may take a few minutes during first startup"
    else
        log "✅ AI models already available"
    fi
}

# Start the application
start_application() {
    log "Starting SynVectorDB githubshare application..."
    
    cd "$SCRIPT_DIR"
    
    # Use existing management script if available
    if [ -f "./manage.sh" ]; then
        ./manage.sh start
    else
        # Fallback to direct streamlit launch
        info "Using direct Streamlit launch"
        cd streamlit_app
        streamlit run Home.py --server.port 8501 --server.address localhost &
        
        # Wait a moment and check if it started
        sleep 3
        if pgrep -f "streamlit run" > /dev/null; then
            log "✅ Application started successfully"
            info "🌐 Access at: http://localhost:8501"
        else
            error "Failed to start application"
            exit 1
        fi
    fi
}

# Fix script permissions
fix_permissions() {
    log "Setting up script permissions..."
    
    # Make sure all scripts are executable
    chmod +x "$SCRIPT_DIR/manage.sh" 2>/dev/null || true
    chmod +x "$SCRIPT_DIR/scripts/download_data.py" 2>/dev/null || true
    chmod +x "$SCRIPT_DIR/setup.sh" 2>/dev/null || true
    
    log "✅ Script permissions configured"
}

# Main setup function
main() {
    echo "🧬 SynVectorDB Local Deployment - Setup & Launch"
    echo "=================================================="
    echo "This script will:"
    echo "1. Check system requirements"
    echo "2. Install Python dependencies" 
    echo "3. Download core database files (~95MB)"
    echo "4. Download optional data files (~55MB)"
    echo "5. Download AI models on first use (~400MB)"
    echo "6. Start the application"
    echo "=================================================="
    
    fix_permissions
    check_requirements
    setup_directories
    install_dependencies
    download_data
    download_models
    start_application
    
    echo ""
    echo "🎉 Setup completed successfully!"
    echo "📊 Application URL: http://localhost:8501"
    echo "📝 Logs directory: $LOGS_DIR"
    echo ""
    echo "To stop the application, run: ./manage.sh stop"
    echo "To check status, run: ./manage.sh status"
}

# Handle command line arguments
case "${1:-setup}" in
    setup|start)
        main
        ;;
    check)
        check_requirements
        ;;
    download)
        download_data
        ;;
    help|--help|-h)
        echo "Usage: $0 [setup|start|check|download|help]"
        echo ""
        echo "Commands:"
        echo "  setup/start  - Full setup and launch (default)"
        echo "  check        - Check system requirements only"
        echo "  download     - Download data files only"
        echo "  help         - Show this help message"
        ;;
    *)
        error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
