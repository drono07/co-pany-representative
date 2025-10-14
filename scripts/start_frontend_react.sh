#!/bin/bash

# React Frontend Startup Script
# Starts the React development server

set -e

echo "🌐 Starting React Frontend..."
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

# Set project root once at the beginning
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if Node.js is installed
check_node() {
    print_status "Checking Node.js installation..."
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_success "Node.js found: $NODE_VERSION"
    else
        print_error "Node.js is not installed. Please install Node.js first:"
        echo "  - Visit: https://nodejs.org/"
        echo "  - Or use: brew install node"
        exit 1
    fi
}

# Check if npm is installed
check_npm() {
    print_status "Checking npm installation..."
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        print_success "npm found: $NPM_VERSION"
    else
        print_error "npm is not installed. Please install npm first."
        exit 1
    fi
}

# Install dependencies
install_dependencies() {
    print_status "Installing React dependencies..."
    # Change to project root directory
    # Change to project root directory
    cd "$PROJECT_ROOT"
    cd frontend
    
    if [ ! -d "node_modules" ]; then
        print_status "Installing dependencies for the first time..."
        npm install
    else
        print_status "Dependencies already installed"
    fi
    
    print_success "Dependencies ready"
    cd ..
}

# Start React development server
start_react() {
    print_status "Starting React development server..."
    # Change to project root directory
    # Change to project root directory
    cd "$PROJECT_ROOT"
    cd frontend
    
    # Set environment variable for API URL
    export REACT_APP_API_URL=http://localhost:8000
    
    # Start the development server
    npm start &
    REACT_PID=$!
    echo $REACT_PID > ../scripts/react.pid
    
    cd ..
    
    sleep 5
    print_success "React development server started (PID: $REACT_PID)"
}

# Cleanup function
cleanup() {
    print_status "Shutting down React frontend..."
    
    # Change to project root directory
    # Change to project root directory
    cd "$PROJECT_ROOT"
    
    if [ -f "scripts/react.pid" ]; then
        REACT_PID=$(cat scripts/react.pid)
        kill $REACT_PID 2>/dev/null || true
        rm -f scripts/react.pid
        print_success "React server stopped"
    fi
    
    print_success "Frontend stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    check_node
    check_npm
    install_dependencies
    start_react
    
    echo ""
    echo "============================="
    print_success "React frontend started!"
    echo ""
    echo "🌐 Frontend Access Points:"
    echo "   React App: http://localhost:3000"
    echo "   Backend API: http://localhost:8000"
    echo ""
    echo "🔧 Services:"
    echo "   React Dev Server: Running (PID: $REACT_PID)"
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
