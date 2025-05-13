#!/bin/bash

# Configuration
STREAMLIT_PORT=8501
API_PORT=8000
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STREAMLIT_APP="streamlit_version/Home.py"
LOG_DIR="${PROJECT_DIR}/logs"
STREAMLIT_PID_FILE="${PROJECT_DIR}/.streamlit.pid"
API_PID_FILE="${PROJECT_DIR}/.api.pid"

# Create log directory
mkdir -p "${LOG_DIR}"

# Color definitions
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check service status
check_service() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null; then
            echo -e "${GREEN}$service_name is running, PID: $pid${NC}"
            return 0
        else
            echo -e "${RED}$service_name has stopped, but PID file still exists${NC}"
            rm -f "$pid_file"
            return 1
        fi
    else
        echo -e "${RED}$service_name is not running${NC}"
        return 1
    fi
}

# Start services
start_services() {
    echo -e "${BLUE}Starting SynVectorDB services...${NC}"
    
    # Check if Streamlit service is already running
    if [ -f "$STREAMLIT_PID_FILE" ]; then
        local pid=$(cat "$STREAMLIT_PID_FILE")
        if ps -p "$pid" > /dev/null; then
            echo -e "${YELLOW}Streamlit service is already running, PID: $pid${NC}"
        else
            echo -e "${YELLOW}Streamlit PID file exists but process is not running, restarting...${NC}"
            rm -f "$STREAMLIT_PID_FILE"
            start_streamlit
        fi
    else
        start_streamlit
    fi
    
    # Check if API service is already running
    if [ -f "$API_PID_FILE" ]; then
        local pid=$(cat "$API_PID_FILE")
        if ps -p "$pid" > /dev/null; then
            echo -e "${YELLOW}API service is already running, PID: $pid${NC}"
        else
            echo -e "${YELLOW}API PID file exists but process is not running, restarting...${NC}"
            rm -f "$API_PID_FILE"
            start_api
        fi
    else
        start_api
    fi
    
    echo -e "${GREEN}Service startup check completed${NC}"
    echo -e "${BLUE}Streamlit service address: ${GREEN}http://localhost:${STREAMLIT_PORT}${NC}"
    echo -e "${BLUE}API service address: ${GREEN}http://localhost:${API_PORT}${NC}"
    echo -e "${YELLOW}View Streamlit logs: ${NC}./start_server.sh logs streamlit"
    echo -e "${YELLOW}View API logs: ${NC}./start_server.sh logs api"
}

# Start Streamlit service
start_streamlit() {
    echo -e "${BLUE}Starting Streamlit service...${NC}"
    cd "$PROJECT_DIR"
    nohup streamlit run "$STREAMLIT_APP" --server.port=$STREAMLIT_PORT > "${LOG_DIR}/streamlit.log" 2>&1 &
    echo $! > "$STREAMLIT_PID_FILE"
    echo -e "${GREEN}Streamlit service started successfully, PID: $(cat $STREAMLIT_PID_FILE)${NC}"
    
    # Wait for service to start
    echo -e "${BLUE}Waiting for Streamlit service to start...${NC}"
    for i in {1..5}; do
        echo -e "${BLUE}Checking Streamlit service status... $i/5${NC}"
        sleep 2
        if curl -s http://localhost:$STREAMLIT_PORT > /dev/null; then
            echo -e "${GREEN}Streamlit service has started successfully${NC}"
            break
        fi
        if [ $i -eq 5 ]; then
            echo -e "${YELLOW}Streamlit service may need more time to start, please check later${NC}"
        fi
    done
}

# Start API service
start_api() {
    echo -e "${BLUE}Starting API service...${NC}"
    cd "$PROJECT_DIR"
    # API service is typically started automatically by Streamlit, but we can also start it separately
    # Here we assume the API service is started automatically by Streamlit, so we don't need additional commands
    # If you need to start the API service separately, uncomment the following lines and modify the command
    # nohup python -m uvicorn api:app --host 0.0.0.0 --port $API_PORT > "${LOG_DIR}/api.log" 2>&1 &
    # echo $! > "$API_PID_FILE"
    # echo -e "${GREEN}API service started successfully, PID: $(cat $API_PID_FILE)${NC}"
    
    # Since the API service is started automatically by Streamlit, we just need to check if the port is available
    echo -e "${BLUE}Waiting for API service to start...${NC}"
    for i in {1..5}; do
        echo -e "${BLUE}Checking API service status... $i/5${NC}"
        sleep 2
        if curl -s http://localhost:$API_PORT > /dev/null; then
            echo -e "${GREEN}API service has started successfully${NC}"
            # Get the PID of the API process
            local api_pid=$(lsof -i:$API_PORT -t)
            if [ -n "$api_pid" ]; then
                echo $api_pid > "$API_PID_FILE"
                echo -e "${GREEN}API service PID: $api_pid${NC}"
            fi
            break
        fi
        if [ $i -eq 5 ]; then
            echo -e "${YELLOW}API service may need more time to start, please check later${NC}"
        fi
    done
}

# Stop services
stop_services() {
    echo -e "${BLUE}Stopping SynVectorDB services...${NC}"
    
    # Stop Streamlit service
    if [ -f "$STREAMLIT_PID_FILE" ]; then
        local pid=$(cat "$STREAMLIT_PID_FILE")
        if ps -p "$pid" > /dev/null; then
            echo -e "${BLUE}Stopping Streamlit service, PID: $pid${NC}"
            kill -15 "$pid"
            sleep 2
            if ps -p "$pid" > /dev/null; then
                echo -e "${YELLOW}Streamlit service did not stop normally, forcing termination${NC}"
                kill -9 "$pid"
            fi
            echo -e "${GREEN}Streamlit service has been stopped${NC}"
        else
            echo -e "${YELLOW}Streamlit service is no longer running${NC}"
        fi
        rm -f "$STREAMLIT_PID_FILE"
    else
        echo -e "${YELLOW}Streamlit service is not running${NC}"
    fi
    
    # Stop API service
    if [ -f "$API_PID_FILE" ]; then
        local pid=$(cat "$API_PID_FILE")
        if ps -p "$pid" > /dev/null; then
            echo -e "${BLUE}Stopping API service, PID: $pid${NC}"
            kill -15 "$pid"
            sleep 2
            if ps -p "$pid" > /dev/null; then
                echo -e "${YELLOW}API service did not stop normally, forcing termination${NC}"
                kill -9 "$pid"
            fi
            echo -e "${GREEN}API service has been stopped${NC}"
        else
            echo -e "${YELLOW}API service is no longer running${NC}"
        fi
        rm -f "$API_PID_FILE"
    else
        echo -e "${YELLOW}API service is not running${NC}"
    fi
    
    echo -e "${GREEN}All services have been stopped${NC}"
}

# Restart services
restart_services() {
    echo -e "${BLUE}Restarting SynVectorDB services...${NC}"
    stop_services
    sleep 2
    start_services
}

# View logs
view_logs() {
    local log_type=$1
    
    case "$log_type" in
        streamlit)
            if [ -f "${LOG_DIR}/streamlit.log" ]; then
                echo -e "${BLUE}Streamlit logs:${NC}"
                tail -f "${LOG_DIR}/streamlit.log"
            else
                echo -e "${RED}Streamlit log file does not exist${NC}"
            fi
            ;;
        api)
            if [ -f "${LOG_DIR}/api.log" ]; then
                echo -e "${BLUE}API logs:${NC}"
                tail -f "${LOG_DIR}/api.log"
            else
                echo -e "${RED}API log file does not exist${NC}"
            fi
            ;;
        *)
            echo -e "${RED}Unknown log type: $log_type${NC}"
            echo -e "${YELLOW}Available log types: streamlit, api${NC}"
            ;;
    esac
}

# Show status
show_status() {
    echo -e "${BLUE}SynVectorDB service status:${NC}"
    check_service "$STREAMLIT_PID_FILE" "Streamlit service"
    check_service "$API_PID_FILE" "API service"
}

# Show help information
show_help() {
    echo -e "${BLUE}SynVectorDB Service Control Script${NC}"
    echo -e "${YELLOW}Usage:${NC}"
    echo -e "  $0 ${GREEN}start${NC}      - Start services"
    echo -e "  $0 ${GREEN}stop${NC}       - Stop services"
    echo -e "  $0 ${GREEN}restart${NC}    - Restart services"
    echo -e "  $0 ${GREEN}status${NC}     - Show service status"
    echo -e "  $0 ${GREEN}logs${NC} TYPE  - View logs (TYPE: streamlit, api)"
    echo -e "  $0 ${GREEN}help${NC}       - Show this help information"
}

# Main function
main() {
    local command=$1
    local arg=$2
    
    case "$command" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            view_logs "$arg"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}"
            show_help
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"
