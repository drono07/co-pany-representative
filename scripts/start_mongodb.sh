#!/bin/bash

# MongoDB Startup Script for Website Analysis Platform
# This script starts MongoDB if it's not already running

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if MongoDB is already running
check_mongodb() {
    if mongosh --eval "db.runCommand('ping')" &> /dev/null; then
        print_success "MongoDB is already running"
        return 0
    else
        return 1
    fi
}

# Start MongoDB using Homebrew service
start_mongodb_service() {
    print_status "Attempting to start MongoDB using Homebrew service..."
    
    if brew services start mongodb-community 2>/dev/null; then
        sleep 3
        if check_mongodb; then
            print_success "MongoDB started successfully via Homebrew service"
            return 0
        fi
    fi
    
    print_warning "Homebrew service failed, trying manual start..."
    return 1
}

# Start MongoDB manually
start_mongodb_manual() {
    print_status "Starting MongoDB manually..."
    
    # Create directories if they don't exist
    mkdir -p /opt/homebrew/var/mongodb
    mkdir -p /opt/homebrew/var/log/mongodb
    
    # Start MongoDB in background
    mongod --dbpath /opt/homebrew/var/mongodb --logpath /opt/homebrew/var/log/mongodb/mongo.log --fork
    
    # Wait a moment for startup
    sleep 3
    
    if check_mongodb; then
        print_success "MongoDB started successfully manually"
        return 0
    else
        print_error "Failed to start MongoDB manually"
        return 1
    fi
}

# Main function
main() {
    echo "==============================================="
    echo "🐘 MongoDB Startup Script"
    echo "==============================================="
    
    # Check if MongoDB is already running
    if check_mongodb; then
        echo "MongoDB is already running and accessible"
        echo "==============================================="
        exit 0
    fi
    
    print_status "MongoDB is not running, attempting to start..."
    
    # Try Homebrew service first
    if start_mongodb_service; then
        echo "==============================================="
        print_success "MongoDB is now running and ready!"
        echo "==============================================="
        exit 0
    fi
    
    # Try manual start
    if start_mongodb_manual; then
        echo "==============================================="
        print_success "MongoDB is now running and ready!"
        echo "==============================================="
        exit 0
    fi
    
    # If we get here, both methods failed
    print_error "Failed to start MongoDB using both methods"
    echo ""
    echo "Manual troubleshooting steps:"
    echo "1. Check if MongoDB is installed: brew list | grep mongodb"
    echo "2. Check MongoDB logs: tail -f /opt/homebrew/var/log/mongodb/mongo.log"
    echo "3. Check if port 27017 is in use: lsof -i :27017"
    echo "4. Try starting manually: mongod --dbpath /opt/homebrew/var/mongodb"
    echo "==============================================="
    exit 1
}

# Run main function
main "$@"
