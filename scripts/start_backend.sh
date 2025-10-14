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

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python
    if command -v python3 &> /dev/null; then
        print_success "Python found: $(python3 --version)"
    else
        print_error "Python 3 is not installed. Please install Python 3 first:"
        echo "  - Visit: https://python.org/"
        echo "  - Or use: brew install python"
        exit 1
    fi
    
    # Check Redis
    if redis-cli ping &> /dev/null; then
        print_success "Redis is running"
    else
        print_error "Redis is not running. Please start Redis first:"
        echo "  - macOS: brew services start redis"
        echo "  - Docker: docker run -d -p 6379:6379 redis:alpine"
        exit 1
    fi
    
    # Check MongoDB
    if mongosh --eval "db.runCommand('ping')" &> /dev/null; then
        print_success "MongoDB is running"
    else
        print_error "MongoDB is not running. Please start MongoDB first:"
        echo "  - macOS: brew services start mongodb-community"
        echo "  - Or manually: mongod --dbpath /opt/homebrew/var/mongodb --logpath /opt/homebrew/var/log/mongodb/mongo.log --fork"
        exit 1
    fi
}

# Start Celery Worker
start_celery_worker() {
    print_status "Starting Celery worker..."
    # Change to project root directory
    cd "$PROJECT_ROOT"
    
    # Check virtual environment
    if [ ! -f "venv/bin/python3" ]; then
        print_error "Virtual environment not found at venv/bin/python3"
        exit 1
    fi
    
    # Use virtual environment Python directly
    VENV_PYTHON="$(pwd)/venv/bin/python3"
    
    # Set PYTHONPATH to include project root
    export PYTHONPATH="$(pwd):$PYTHONPATH"
    
    $VENV_PYTHON backend/tasks/celery_worker.py &
    CELERY_WORKER_PID=$!
    echo $CELERY_WORKER_PID > scripts/celery_worker.pid
    sleep 2
    print_success "Celery worker started (PID: $CELERY_WORKER_PID)"
}

# Start Celery Beat
start_celery_beat() {
    print_status "Starting Celery beat scheduler..."
    # Change to project root directory
    cd "$PROJECT_ROOT"
    
    # Check virtual environment
    if [ ! -f "venv/bin/python3" ]; then
        print_error "Virtual environment not found at venv/bin/python3"
        exit 1
    fi
    
    # Use virtual environment Python directly
    VENV_PYTHON="$(pwd)/venv/bin/python3"
    
    # Set PYTHONPATH to include project root
    export PYTHONPATH="$(pwd):$PYTHONPATH"
    
    $VENV_PYTHON backend/tasks/celery_beat.py &
    CELERY_BEAT_PID=$!
    echo $CELERY_BEAT_PID > scripts/celery_beat.pid
    sleep 2
    print_success "Celery beat started (PID: $CELERY_BEAT_PID)"
}

# Start FastAPI
start_fastapi() {
    print_status "Starting FastAPI server..."
    # Change to project root directory
    cd "$PROJECT_ROOT"
    
    # Check virtual environment
    if [ ! -f "venv/bin/python3" ]; then
        print_error "Virtual environment not found at venv/bin/python3"
        exit 1
    fi
    
    # Use virtual environment Python directly
    VENV_PYTHON="$(pwd)/venv/bin/python3"
    
    # Set PYTHONPATH to include project root
    export PYTHONPATH="$(pwd):$PYTHONPATH"
    
    $VENV_PYTHON -m uvicorn backend.api.fastapi_app:app --host 0.0.0.0 --port 8000 --reload &
    FASTAPI_PID=$!
    echo $FASTAPI_PID > scripts/fastapi.pid
    sleep 3
    print_success "FastAPI server started (PID: $FASTAPI_PID)"
}

# Cleanup function
cleanup() {
    print_status "Shutting down backend services..."
    
    # Change to project root directory
    cd "$PROJECT_ROOT"
    
    if [ -f "scripts/fastapi.pid" ]; then
        FASTAPI_PID=$(cat scripts/fastapi.pid)
        kill $FASTAPI_PID 2>/dev/null || true
        rm -f scripts/fastapi.pid
        print_success "FastAPI stopped"
    fi
    
    if [ -f "scripts/celery_beat.pid" ]; then
        CELERY_BEAT_PID=$(cat scripts/celery_beat.pid)
        kill $CELERY_BEAT_PID 2>/dev/null || true
        rm -f scripts/celery_beat.pid
        print_success "Celery beat stopped"
    fi
    
    if [ -f "scripts/celery_worker.pid" ]; then
        CELERY_WORKER_PID=$(cat scripts/celery_worker.pid)
        kill $CELERY_WORKER_PID 2>/dev/null || true
        rm -f scripts/celery_worker.pid
        print_success "Celery worker stopped"
    fi
    
    print_success "Backend services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Set project root once at the beginning
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Main execution
main() {
    check_prerequisites
    
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
