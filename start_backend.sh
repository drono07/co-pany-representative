#!/bin/bash

# Backend Startup Script
# Starts only the backend services (Celery + FastAPI)

set -e

echo "🚀 Starting Backend Services..."
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Redis
check_redis() {
    print_status "Checking Redis connection..."
    if ! redis-cli ping &> /dev/null; then
        print_error "Redis is not running. Please start Redis first:"
        echo "  - macOS: brew services start redis"
        echo "  - Docker: docker run -d -p 6379:6379 redis:alpine"
        exit 1
    fi
    print_success "Redis is running"
}

# Start Celery Worker
start_celery_worker() {
    print_status "Starting Celery worker..."
    python3 celery_worker.py &
    CELERY_WORKER_PID=$!
    echo $CELERY_WORKER_PID > celery_worker.pid
    sleep 2
    print_success "Celery worker started (PID: $CELERY_WORKER_PID)"
}

# Start Celery Beat
start_celery_beat() {
    print_status "Starting Celery beat scheduler..."
    python3 celery_beat.py &
    CELERY_BEAT_PID=$!
    echo $CELERY_BEAT_PID > celery_beat.pid
    sleep 2
    print_success "Celery beat started (PID: $CELERY_BEAT_PID)"
}

# Start FastAPI
start_fastapi() {
    print_status "Starting FastAPI server..."
    python3 -m uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload &
    FASTAPI_PID=$!
    echo $FASTAPI_PID > fastapi.pid
    sleep 3
    print_success "FastAPI server started (PID: $FASTAPI_PID)"
}

# Cleanup function
cleanup() {
    print_status "Shutting down backend services..."
    
    if [ -f "fastapi.pid" ]; then
        FASTAPI_PID=$(cat fastapi.pid)
        kill $FASTAPI_PID 2>/dev/null || true
        rm -f fastapi.pid
        print_success "FastAPI stopped"
    fi
    
    if [ -f "celery_beat.pid" ]; then
        CELERY_BEAT_PID=$(cat celery_beat.pid)
        kill $CELERY_BEAT_PID 2>/dev/null || true
        rm -f celery_beat.pid
        print_success "Celery beat stopped"
    fi
    
    if [ -f "celery_worker.pid" ]; then
        CELERY_WORKER_PID=$(cat celery_worker.pid)
        kill $CELERY_WORKER_PID 2>/dev/null || true
        rm -f celery_worker.pid
        print_success "Celery worker stopped"
    fi
    
    print_success "Backend services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    check_redis
    
    echo ""
    print_status "Starting backend services..."
    start_celery_worker
    start_celery_beat
    start_fastapi
    
    echo ""
    echo "==============================="
    print_success "Backend services started!"
    echo ""
    echo "📊 Backend Access Points:"
    echo "   API Server: http://localhost:8000"
    echo "   API Docs:   http://localhost:8000/docs"
    echo "   Health:     http://localhost:8000/health"
    echo ""
    echo "🔧 Services:"
    echo "   Celery Worker: Running (PID: $CELERY_WORKER_PID)"
    echo "   Celery Beat:   Running (PID: $CELERY_BEAT_PID)"
    echo "   FastAPI:       Running (PID: $FASTAPI_PID)"
    echo ""
    echo "Press Ctrl+C to stop backend services"
    echo "==============================="
    
    # Wait for interrupt
    while true; do
        sleep 1
    done
}

# Run main function
main
