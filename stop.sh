#!/bin/bash

# Stop Script for Website Analysis Platform
# Stops all running services

set -e

echo "🛑 Stopping Website Analysis Platform..."
echo "======================================"

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

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Stop processes by PID files
stop_by_pid() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            print_status "Stopping $service_name (PID: $pid)..."
            kill $pid 2>/dev/null || true
            sleep 2
            
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                print_warning "Force killing $service_name..."
                kill -9 $pid 2>/dev/null || true
            fi
            
            print_success "$service_name stopped"
        else
            print_warning "$service_name was not running"
        fi
        rm -f "$pid_file"
    else
        print_warning "No PID file found for $service_name"
    fi
}

# Stop all services
stop_all_services() {
    print_status "Stopping all services..."
    
    # Stop by PID files
    stop_by_pid "FastAPI" "fastapi.pid"
    stop_by_pid "Celery Beat" "celery_beat.pid"
    stop_by_pid "Celery Worker" "celery_worker.pid"
    stop_by_pid "HTTP Server" "http_server.pid"
    
    # Kill any remaining processes
    print_status "Cleaning up any remaining processes..."
    
    # Kill FastAPI processes
    pkill -f "uvicorn.*fastapi_app" 2>/dev/null || true
    
    # Kill Celery processes
    pkill -f "celery.*worker" 2>/dev/null || true
    pkill -f "celery.*beat" 2>/dev/null || true
    
    # Kill HTTP server processes
    pkill -f "python.*http.server" 2>/dev/null || true
    
    # Kill processes on specific ports
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_status "Killing processes on port 8000..."
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    fi
    
    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_status "Killing processes on port 3000..."
        lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    fi
    
    print_success "All services stopped"
}

# Main execution
main() {
    stop_all_services
    
    echo ""
    echo "======================================"
    print_success "Platform stopped successfully!"
    echo "======================================"
}

# Run main function
main
