#!/bin/bash

# Test Script for Website Analysis Platform
# Tests the platform functionality

set -e

echo "🧪 Testing Website Analysis Platform..."
echo "====================================="

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

# Check if backend is running
check_backend() {
    print_status "Checking if backend is running..."
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "Backend is running"
        return 0
    else
        print_error "Backend is not running. Please start it first:"
        echo "  ./start_backend.sh"
        return 1
    fi
}

# Run tests
run_tests() {
    print_status "Running platform tests..."
    
    if python3 test_celery_platform.py; then
        print_success "All tests passed!"
    else
        print_error "Some tests failed"
        exit 1
    fi
}

# Main execution
main() {
    if check_backend; then
        run_tests
    else
        exit 1
    fi
}

# Run main function
main
