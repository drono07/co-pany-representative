#!/bin/bash

# Frontend Startup Script
# Starts a simple HTTP server for the dashboard

set -e

echo "🌐 Starting Frontend Server..."
echo "============================="

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

# Check if dashboard.html exists
check_dashboard() {
    if [ ! -f "dashboard.html" ]; then
        print_error "dashboard.html not found. Please ensure the dashboard file exists."
        exit 1
    fi
    print_success "Dashboard file found"
}

# Start HTTP server
start_http_server() {
    print_status "Starting HTTP server for frontend..."
    
    # Try Python 3 first, then Python 2
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python."
        exit 1
    fi
    
    # Start HTTP server
    $PYTHON_CMD -m http.server 3000 &
    HTTP_PID=$!
    echo $HTTP_PID > http_server.pid
    sleep 2
    print_success "HTTP server started (PID: $HTTP_PID)"
}

# Cleanup function
cleanup() {
    print_status "Shutting down frontend server..."
    
    if [ -f "http_server.pid" ]; then
        HTTP_PID=$(cat http_server.pid)
        kill $HTTP_PID 2>/dev/null || true
        rm -f http_server.pid
        print_success "HTTP server stopped"
    fi
    
    print_success "Frontend server stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    check_dashboard
    start_http_server
    
    echo ""
    echo "============================="
    print_success "Frontend server started!"
    echo ""
    echo "🌐 Frontend Access Points:"
    echo "   Dashboard: http://localhost:3000/dashboard.html"
    echo "   Static Files: http://localhost:3000/"
    echo ""
    echo "📊 Backend API (if running):"
    echo "   API Server: http://localhost:8000"
    echo "   API Docs:   http://localhost:8000/docs"
    echo ""
    echo "🔧 Services:"
    echo "   HTTP Server: Running (PID: $HTTP_PID)"
    echo ""
    echo "Press Ctrl+C to stop frontend server"
    echo "============================="
    
    # Wait for interrupt
    while true; do
        sleep 1
    done
}

# Run main function
main
