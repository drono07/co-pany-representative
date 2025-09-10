#!/bin/bash

# Website Analysis Platform Startup Script
# This script sets up and starts all required services

set -e  # Exit on any error

echo "🚀 Starting Website Analysis Platform..."
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is installed
check_python() {
    print_status "Checking Python installation..."
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python 3.8+"
        exit 1
    fi
    print_success "Python found: $($PYTHON_CMD --version)"
}

# Check if Redis is running
check_redis() {
    print_status "Checking Redis connection..."
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            print_success "Redis is running"
            return 0
        fi
    fi
    
    print_warning "Redis is not running. Attempting to start..."
    
    # Try different methods to start Redis
    if command -v brew &> /dev/null; then
        print_status "Starting Redis with Homebrew..."
        brew services start redis
        sleep 2
        if redis-cli ping &> /dev/null; then
            print_success "Redis started with Homebrew"
            return 0
        fi
    fi
    
    if command -v docker &> /dev/null; then
        print_status "Starting Redis with Docker..."
        docker run -d -p 6379:6379 --name redis-website-analysis redis:alpine
        sleep 3
        if redis-cli ping &> /dev/null; then
            print_success "Redis started with Docker"
            return 0
        fi
    fi
    
    print_error "Could not start Redis. Please start Redis manually:"
    echo "  - macOS: brew services start redis"
    echo "  - Docker: docker run -d -p 6379:6379 redis:alpine"
    echo "  - Ubuntu: sudo systemctl start redis-server"
    exit 1
}

# Install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    if [ -f "requirements_fastapi.txt" ]; then
        $PYTHON_CMD -m pip install -r requirements_fastapi.txt
        print_success "Dependencies installed"
    else
        print_error "requirements_fastapi.txt not found"
        exit 1
    fi
}

# Setup database
setup_database() {
    print_status "Setting up database..."
    $PYTHON_CMD -c "
import asyncio
from database_schema import get_database

async def setup():
    try:
        db = await get_database()
        print('Database setup completed!')
    except Exception as e:
        print(f'Database setup failed: {e}')
        exit(1)

asyncio.run(setup())
"
    print_success "Database setup completed"
}

# Start Celery Worker
start_celery_worker() {
    print_status "Starting Celery worker..."
    $PYTHON_CMD celery_worker.py &
    CELERY_WORKER_PID=$!
    echo $CELERY_WORKER_PID > celery_worker.pid
    sleep 2
    print_success "Celery worker started (PID: $CELERY_WORKER_PID)"
}

# Start Celery Beat
start_celery_beat() {
    print_status "Starting Celery beat scheduler..."
    
    # Kill any existing beat processes
    pkill -f "celery.*beat" 2>/dev/null || true
    sleep 1
    
    $PYTHON_CMD celery_beat.py &
    CELERY_BEAT_PID=$!
    echo $CELERY_BEAT_PID > celery_beat.pid
    sleep 3
    
    # Verify beat started successfully
    if ps -p $CELERY_BEAT_PID > /dev/null; then
        print_success "Celery beat started (PID: $CELERY_BEAT_PID)"
    else
        print_error "Celery beat failed to start"
        return 1
    fi
}

# Start FastAPI
start_fastapi() {
    print_status "Starting FastAPI server..."
    
    # Check if port 8000 is already in use
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
        print_warning "Port 8000 is already in use. Trying to kill existing process..."
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
    
    $PYTHON_CMD -m uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload &
    FASTAPI_PID=$!
    echo $FASTAPI_PID > fastapi.pid
    sleep 3
    
    # Verify FastAPI started successfully
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "FastAPI server started (PID: $FASTAPI_PID)"
    else
        print_error "FastAPI server failed to start properly"
        return 1
    fi
}

# Cleanup function
cleanup() {
    print_status "Shutting down services..."
    
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
    
    print_success "All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    echo ""
    print_status "Checking prerequisites..."
    check_python
    check_redis
    
    echo ""
    print_status "Setting up platform..."
    install_dependencies
    setup_database
    
    echo ""
    print_status "Starting services..."
    start_celery_worker
    start_celery_beat
    start_fastapi
    
    echo ""
    echo "========================================"
    print_success "Platform started successfully!"
    echo ""
    echo "📊 Access Points:"
    echo "   React App:  http://localhost:3000"
    echo "   API Server: http://localhost:8000"
    echo "   API Docs:   http://localhost:8000/docs"
    echo "   Redis:      localhost:6379"
    echo ""
    echo "🔧 Services:"
    echo "   Celery Worker: Running (PID: $CELERY_WORKER_PID)"
    echo "   Celery Beat:   Running (PID: $CELERY_BEAT_PID)"
    echo "   FastAPI:       Running (PID: $FASTAPI_PID)"
    echo ""
    echo "Press Ctrl+C to stop all services"
    echo "========================================"
    
    # Wait for interrupt
    while true; do
        sleep 1
    done
}

# Run main function
main
