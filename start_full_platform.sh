#!/bin/bash

# Complete Platform Startup Script
# Starts backend (Celery + FastAPI) and frontend (React)

set -e

echo "🚀 Starting Complete Website Analysis Platform..."
echo "==============================================="

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

# Clean up existing processes
cleanup_existing_processes() {
    print_status "Cleaning up existing processes..."
    
    # Kill existing processes by name (more aggressive)
    print_status "Killing processes by name patterns..."
    pkill -f "uvicorn.*fastapi_app" 2>/dev/null || true
    pkill -f "celery.*worker" 2>/dev/null || true
    pkill -f "celery.*beat" 2>/dev/null || true
    pkill -f "react-scripts" 2>/dev/null || true
    pkill -f "celery_worker.py" 2>/dev/null || true
    pkill -f "celery_beat.py" 2>/dev/null || true
    pkill -f "fastapi_app" 2>/dev/null || true
    
    # Kill processes on specific ports (more thorough)
    print_status "Killing processes on ports 8000 and 3000..."
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_status "Killing processes on port 8000..."
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    fi
    
    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_status "Killing processes on port 3000..."
        lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    fi
    
    # Kill any remaining Python processes that might be related
    print_status "Killing any remaining related Python processes..."
    pkill -f "python.*celery" 2>/dev/null || true
    pkill -f "python.*uvicorn" 2>/dev/null || true
    
    # Remove PID files
    print_status "Removing PID files..."
    rm -f fastapi.pid celery_worker.pid celery_beat.pid react.pid
    
    # Wait longer for cleanup to complete
    print_status "Waiting for cleanup to complete..."
    sleep 3
    
    # Verify cleanup
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_error "Port 8000 is still in use after cleanup!"
        lsof -Pi :8000
    fi
    
    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_error "Port 3000 is still in use after cleanup!"
        lsof -Pi :3000
    fi
    
    print_success "Cleanup completed"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python 3.8+"
        exit 1
    fi
    print_success "Python found: $($PYTHON_CMD --version)"
    
    # Check Node.js
    if command -v node &> /dev/null; then
        print_success "Node.js found: $(node --version)"
    else
        print_error "Node.js is not installed. Please install Node.js first:"
        echo "  - Visit: https://nodejs.org/"
        echo "  - Or use: brew install node"
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
}

# Start backend services
start_backend() {
    print_status "Starting backend services..."
    
    # Start Celery worker
    $PYTHON_CMD celery_worker.py &
    CELERY_WORKER_PID=$!
    echo $CELERY_WORKER_PID > celery_worker.pid
    sleep 2
    print_success "Celery worker started (PID: $CELERY_WORKER_PID)"
    
    # Start Celery beat
    $PYTHON_CMD celery_beat.py &
    CELERY_BEAT_PID=$!
    echo $CELERY_BEAT_PID > celery_beat.pid
    sleep 2
    print_success "Celery beat started (PID: $CELERY_BEAT_PID)"
    
    # Start FastAPI
    $PYTHON_CMD -m uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload &
    FASTAPI_PID=$!
    echo $FASTAPI_PID > fastapi.pid
    sleep 3
    print_success "FastAPI server started (PID: $FASTAPI_PID)"
}

# Start frontend
start_frontend() {
    print_status "Starting React frontend..."
    
    cd frontend
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        print_status "Installing React dependencies..."
        npm install
    fi
    
    # Set environment variable
    export REACT_APP_API_URL=http://localhost:8000
    
    # Start React development server
    npm start &
    REACT_PID=$!
    echo $REACT_PID > ../react.pid
    
    cd ..
    
    sleep 5
    print_success "React frontend started (PID: $REACT_PID)"
}

# Cleanup function
cleanup() {
    print_status "Shutting down all services..."
    
    # Stop React
    if [ -f "react.pid" ]; then
        REACT_PID=$(cat react.pid)
        if ps -p $REACT_PID > /dev/null 2>&1; then
            kill $REACT_PID 2>/dev/null || true
            sleep 1
            if ps -p $REACT_PID > /dev/null 2>&1; then
                kill -9 $REACT_PID 2>/dev/null || true
            fi
        fi
        rm -f react.pid
        print_success "React frontend stopped"
    fi
    
    # Stop FastAPI
    if [ -f "fastapi.pid" ]; then
        FASTAPI_PID=$(cat fastapi.pid)
        if ps -p $FASTAPI_PID > /dev/null 2>&1; then
            kill $FASTAPI_PID 2>/dev/null || true
            sleep 1
            if ps -p $FASTAPI_PID > /dev/null 2>&1; then
                kill -9 $FASTAPI_PID 2>/dev/null || true
            fi
        fi
        rm -f fastapi.pid
        print_success "FastAPI stopped"
    fi
    
    # Stop Celery beat
    if [ -f "celery_beat.pid" ]; then
        CELERY_BEAT_PID=$(cat celery_beat.pid)
        if ps -p $CELERY_BEAT_PID > /dev/null 2>&1; then
            kill $CELERY_BEAT_PID 2>/dev/null || true
            sleep 1
            if ps -p $CELERY_BEAT_PID > /dev/null 2>&1; then
                kill -9 $CELERY_BEAT_PID 2>/dev/null || true
            fi
        fi
        rm -f celery_beat.pid
        print_success "Celery beat stopped"
    fi
    
    # Stop Celery worker
    if [ -f "celery_worker.pid" ]; then
        CELERY_WORKER_PID=$(cat celery_worker.pid)
        if ps -p $CELERY_WORKER_PID > /dev/null 2>&1; then
            kill $CELERY_WORKER_PID 2>/dev/null || true
            sleep 1
            if ps -p $CELERY_WORKER_PID > /dev/null 2>&1; then
                kill -9 $CELERY_WORKER_PID 2>/dev/null || true
            fi
        fi
        rm -f celery_worker.pid
        print_success "Celery worker stopped"
    fi
    
    # Additional cleanup - kill any remaining processes (more aggressive)
    print_status "Performing additional cleanup..."
    pkill -f "uvicorn.*fastapi_app" 2>/dev/null || true
    pkill -f "celery.*worker" 2>/dev/null || true
    pkill -f "celery.*beat" 2>/dev/null || true
    pkill -f "react-scripts" 2>/dev/null || true
    pkill -f "celery_worker.py" 2>/dev/null || true
    pkill -f "celery_beat.py" 2>/dev/null || true
    pkill -f "fastapi_app" 2>/dev/null || true
    pkill -f "python.*celery" 2>/dev/null || true
    pkill -f "python.*uvicorn" 2>/dev/null || true
    
    # Kill processes on specific ports
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_status "Force killing processes on port 8000..."
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    fi
    
    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_status "Force killing processes on port 3000..."
        lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    fi
    
    print_success "All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    cleanup_existing_processes
    check_prerequisites
    start_backend
    start_frontend
    
    echo ""
    echo "==============================================="
    print_success "Complete platform started successfully!"
    echo ""
    echo "🌐 Access Points:"
    echo "   React App:  http://localhost:3000"
    echo "   API Server: http://localhost:8000"
    echo "   API Docs:   http://localhost:8000/docs"
    echo "   Redis:      localhost:6379"
    echo ""
    echo "🔧 Services:"
    echo "   React Frontend: Running (PID: $REACT_PID)"
    echo "   FastAPI:        Running (PID: $FASTAPI_PID)"
    echo "   Celery Worker:  Running (PID: $CELERY_WORKER_PID)"
    echo "   Celery Beat:    Running (PID: $CELERY_BEAT_PID)"
    echo ""
    echo "📱 Features:"
    echo "   ✅ User Authentication"
    echo "   ✅ Application Management"
    echo "   ✅ Real-time Analysis"
    echo "   ✅ Task Monitoring"
    echo "   ✅ Dashboard & Charts"
    echo "   ✅ Automated Scheduling"
    echo ""
    echo "Press Ctrl+C to stop all services"
    echo "==============================================="
    
    # Wait for interrupt
    while true; do
        sleep 1
    done
}

# Run main function
main
