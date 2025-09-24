#!/bin/bash
# SynVectorDB Docker Test Script
# Comprehensive testing of Docker deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="synvectordb-githubshare"
IMAGE_NAME="synvectordb-githubshare"
TEST_PORT="8501"
HEALTH_TIMEOUT=120

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Cleanup function
cleanup() {
    log "Cleaning up Docker resources..."
    docker-compose down --remove-orphans 2>/dev/null || true
    docker container rm -f "$CONTAINER_NAME" 2>/dev/null || true
}

# Test Docker build
test_docker_build() {
    log "Testing Docker build..."
    
    if docker build -t "$IMAGE_NAME" .; then
        success "Docker image built successfully"
        
        # Check image size
        IMAGE_SIZE=$(docker images "$IMAGE_NAME" --format "table {{.Size}}" | tail -n 1)
        log "Image size: $IMAGE_SIZE"
        
        return 0
    else
        error "Docker build failed"
        return 1
    fi
}

# Test Docker run
test_docker_run() {
    log "Testing Docker container startup..."
    
    # Start container
    if docker run -d --name "$CONTAINER_NAME" -p "$TEST_PORT:8501" "$IMAGE_NAME"; then
        success "Container started successfully"
    else
        error "Failed to start container"
        return 1
    fi
    
    # Wait for container to be ready
    log "Waiting for container to be ready..."
    local count=0
    while [ $count -lt $HEALTH_TIMEOUT ]; do
        if docker exec "$CONTAINER_NAME" curl -f http://localhost:8501/healthz >/dev/null 2>&1; then
            success "Container is healthy and responding"
            return 0
        fi
        
        if [ $((count % 10)) -eq 0 ]; then
            log "Still waiting... ($count/${HEALTH_TIMEOUT}s)"
        fi
        
        sleep 1
        count=$((count + 1))
    done
    
    error "Container failed to become healthy within ${HEALTH_TIMEOUT}s"
    
    # Show container logs for debugging
    log "Container logs:"
    docker logs "$CONTAINER_NAME" --tail 20
    
    return 1
}

# Test application functionality
test_application() {
    log "Testing application functionality..."
    
    # Test main page
    if curl -f -s "http://localhost:$TEST_PORT" >/dev/null; then
        success "Main page accessible"
    else
        error "Main page not accessible"
        return 1
    fi
    
    # Test health endpoint
    if curl -f -s "http://localhost:$TEST_PORT/healthz" >/dev/null; then
        success "Health endpoint responding"
    else
        warning "Health endpoint not responding"
    fi
    
    # Test database functionality inside container
    log "Testing database functionality inside container..."
    if docker exec "$CONTAINER_NAME" python3 test_suite.py >/dev/null 2>&1; then
        success "Database tests passed inside container"
    else
        warning "Database tests failed inside container"
        # Show test output for debugging
        docker exec "$CONTAINER_NAME" python3 test_suite.py || true
    fi
    
    return 0
}

# Test Docker Compose
test_docker_compose() {
    log "Testing Docker Compose deployment..."
    
    # Cleanup any existing containers
    cleanup
    
    # Start with docker-compose
    if docker-compose up -d; then
        success "Docker Compose started successfully"
    else
        error "Docker Compose failed to start"
        return 1
    fi
    
    # Wait for service to be ready
    log "Waiting for Docker Compose service to be ready..."
    local count=0
    while [ $count -lt $HEALTH_TIMEOUT ]; do
        if curl -f -s "http://localhost:$TEST_PORT" >/dev/null 2>&1; then
            success "Docker Compose service is ready"
            return 0
        fi
        
        if [ $((count % 10)) -eq 0 ]; then
            log "Still waiting... ($count/${HEALTH_TIMEOUT}s)"
        fi
        
        sleep 1
        count=$((count + 1))
    done
    
    error "Docker Compose service failed to become ready"
    
    # Show service logs
    log "Service logs:"
    docker-compose logs --tail 20
    
    return 1
}

# Performance test
test_performance() {
    log "Running performance tests..."
    
    # Test response time
    local response_time
    response_time=$(curl -o /dev/null -s -w '%{time_total}' "http://localhost:$TEST_PORT")
    
    log "Response time: ${response_time}s"
    
    if (( $(echo "$response_time < 5.0" | bc -l) )); then
        success "Response time acceptable (< 5s)"
    else
        warning "Response time slow (> 5s)"
    fi
    
    # Test concurrent requests
    log "Testing concurrent requests..."
    for i in {1..5}; do
        curl -s "http://localhost:$TEST_PORT" >/dev/null &
    done
    wait
    
    success "Concurrent requests completed"
    
    return 0
}

# Main test function
run_tests() {
    log "Starting comprehensive Docker tests..."
    
    local tests_passed=0
    local total_tests=5
    
    # Test 1: Docker build
    if test_docker_build; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test 2: Docker run
    if test_docker_run; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test 3: Application functionality
    if test_application; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test 4: Performance
    if test_performance; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Cleanup standalone container
    docker container rm -f "$CONTAINER_NAME" 2>/dev/null || true
    
    # Test 5: Docker Compose
    if test_docker_compose; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Results
    log "Docker tests completed"
    log "Tests passed: $tests_passed/$total_tests"
    
    if [ $tests_passed -eq $total_tests ]; then
        success "🎉 ALL DOCKER TESTS PASSED!"
        log "Docker deployment is ready for production"
        return 0
    else
        error "⚠️  SOME DOCKER TESTS FAILED"
        log "Please review and fix issues before deployment"
        return 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        exit 1
    fi
    
    # Check required files
    if [ ! -f "Dockerfile" ]; then
        error "Dockerfile not found"
        exit 1
    fi
    
    if [ ! -f "docker-compose.yml" ]; then
        error "docker-compose.yml not found"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -c, --cleanup  Cleanup Docker resources and exit"
    echo "  -b, --build    Only test Docker build"
    echo "  -r, --run      Only test Docker run"
    echo "  -t, --test     Only test application functionality"
    echo "  -p, --perf     Only test performance"
    echo "  -d, --compose  Only test Docker Compose"
    echo ""
    echo "Examples:"
    echo "  $0              # Run all tests"
    echo "  $0 --build      # Test only Docker build"
    echo "  $0 --cleanup    # Cleanup Docker resources"
}

# Main script
main() {
    case "${1:-}" in
        -h|--help)
            show_usage
            exit 0
            ;;
        -c|--cleanup)
            cleanup
            success "Cleanup completed"
            exit 0
            ;;
        -b|--build)
            check_prerequisites
            test_docker_build
            exit $?
            ;;
        -r|--run)
            check_prerequisites
            test_docker_run
            cleanup
            exit $?
            ;;
        -t|--test)
            test_application
            exit $?
            ;;
        -p|--perf)
            test_performance
            exit $?
            ;;
        -d|--compose)
            check_prerequisites
            test_docker_compose
            cleanup
            exit $?
            ;;
        "")
            check_prerequisites
            run_tests
            result=$?
            cleanup
            exit $result
            ;;
        *)
            error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Trap cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"
