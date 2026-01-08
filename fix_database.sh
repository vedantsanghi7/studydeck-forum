#!/bin/bash

# Script to fix database issues on EC2
# Run this on your EC2 server

set -e

echo "=========================================="
echo "Fixing Database Issues"
echo "=========================================="
echo ""

# Make sure we're in the project directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "Error: docker-compose.prod.yml not found!"
    echo "Please run this from the project directory: cd ~/studydeck"
    exit 1
fi

echo "Step 1: Stopping containers..."
docker-compose -f docker-compose.prod.yml down

echo ""
echo "Step 2: Removing old database volume (if exists)..."
docker volume rm studydeck_postgres_data 2>/dev/null || echo "Volume doesn't exist (that's ok)"

echo ""
echo "Step 3: Checking .env file..."
if [ ! -f ".env" ]; then
    echo "Error: .env file not found!"
    exit 1
fi

# Check if POSTGRES_PASSWORD is set
if ! grep -q "^POSTGRES_PASSWORD=" .env; then
    echo "Error: POSTGRES_PASSWORD not found in .env file!"
    exit 1
fi

echo "✓ .env file found"

echo ""
echo "Step 4: Starting database container first..."
docker-compose -f docker-compose.prod.yml up -d db

echo ""
echo "Waiting for database to be ready..."
sleep 5

echo ""
echo "Step 5: Checking if database was created..."
docker-compose -f docker-compose.prod.yml exec -T db psql -U studydeck_user -d studydeck_db -c "SELECT 1;" 2>&1 || {
    echo ""
    echo "Database doesn't exist yet. Creating it..."
    docker-compose -f docker-compose.prod.yml exec -T db psql -U studydeck_user -d postgres -c "CREATE DATABASE studydeck_db;" 2>&1 || echo "Database might already exist"
}

echo ""
echo "Step 6: Verifying database connection..."
docker-compose -f docker-compose.prod.yml exec -T db psql -U studydeck_user -d studydeck_db -c "SELECT version();" > /dev/null 2>&1 && {
    echo "✓ Database connection successful!"
} || {
    echo "✗ Database connection failed!"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check database logs: docker-compose -f docker-compose.prod.yml logs db"
    echo "2. Check if POSTGRES_PASSWORD is set correctly in .env"
    exit 1
}

echo ""
echo "Step 7: Starting all services..."
docker-compose -f docker-compose.prod.yml up -d

echo ""
echo "=========================================="
echo "Done!"
echo "=========================================="
echo ""
echo "Check logs: docker-compose -f docker-compose.prod.yml logs -f"
echo ""
