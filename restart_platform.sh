#!/bin/bash

# Restart Script for Website Analysis Platform
# Stops all services and starts them again

set -e

echo "🔄 Restarting Website Analysis Platform..."
echo "=========================================="

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

# Stop all services
print_status "Stopping all services..."
./stop.sh

# Wait a moment for cleanup
sleep 3

# Start all services
print_status "Starting all services..."
./start_full_platform.sh
