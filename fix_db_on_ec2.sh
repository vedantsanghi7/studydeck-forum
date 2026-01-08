#!/bin/bash

# Diagnostic and fix script for database issues on EC2
# Run this ON your EC2 server: ./fix_db_on_ec2.sh

set -e

echo "=========================================="
echo "Database Diagnostic & Fix Script"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.prod.yml" ]; then
    echo "Error: docker-compose.prod.yml not found!"
    echo "Please run from project directory: cd ~/studydeck"
    exit 1
fi

echo "Step 1: Checking .env file..."
if [ ! -f ".env" ]; then
    echo "✗ .env file not found!"
    exit 1
fi

echo "✓ .env file found"
echo ""

echo "Step 2: Checking DATABASE_URL in .env..."
DATABASE_URL=$(grep "^DATABASE_URL=" .env | cut -d '=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || echo "")
if [ -z "$DATABASE_URL" ]; then
    echo "✗ DATABASE_URL not found in .env"
    exit 1
fi

echo "✓ DATABASE_URL found: ${DATABASE_URL:0:50}..."
echo ""

# Extract database name from DATABASE_URL
DB_NAME=$(echo "$DATABASE_URL" | sed -n 's|.*/\([^?]*\)$|\1|p' | sed 's/[[:space:]]*$//')

echo "Step 3: Extracted database name: $DB_NAME"
echo ""

echo "Step 4: Checking if database exists..."
DB_EXISTS=$(docker-compose -f docker-compose.prod.yml exec -T db psql -U studydeck_user -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null || echo "0")

if [ "$DB_EXISTS" = "1" ]; then
    echo "✓ Database '$DB_NAME' exists"
else
    echo "✗ Database '$DB_NAME' does not exist"
    echo "Creating database..."
    docker-compose -f docker-compose.prod.yml exec -T db psql -U studydeck_user -d postgres -c "CREATE DATABASE $DB_NAME;" 2>&1 || echo "Database might already exist"
    echo "✓ Database created"
fi
echo ""

echo "Step 5: Checking what Django sees..."
WEB_DATABASE_URL=$(docker-compose -f docker-compose.prod.yml exec -T web env | grep "^DATABASE_URL=" | cut -d '=' -f2- || echo "")

if [ -z "$WEB_DATABASE_URL" ]; then
    echo "✗ DATABASE_URL not found in web container environment"
    echo "This means .env is not being read properly"
    echo ""
    echo "Fixing: Restarting web container to reload .env..."
    docker-compose -f docker-compose.prod.yml restart web
    sleep 3
    WEB_DATABASE_URL=$(docker-compose -f docker-compose.prod.yml exec -T web env | grep "^DATABASE_URL=" | cut -d '=' -f2- || echo "")
    if [ -z "$WEB_DATABASE_URL" ]; then
        echo "✗ Still not found. Rebuilding containers..."
        docker-compose -f docker-compose.prod.yml down
        docker-compose -f docker-compose.prod.yml up -d --build
        sleep 5
    fi
else
    echo "✓ DATABASE_URL found in web container: ${WEB_DATABASE_URL:0:50}..."
    
    # Extract database name from web container's DATABASE_URL
    WEB_DB_NAME=$(echo "$WEB_DATABASE_URL" | sed -n 's|.*/\([^?]*\)$|\1|p' | sed 's/[[:space:]]*$//')
    echo "   Database name in web container: $WEB_DB_NAME"
    
    if [ "$WEB_DB_NAME" != "$DB_NAME" ]; then
        echo "✗ Mismatch! .env has '$DB_NAME' but web container has '$WEB_DB_NAME'"
        echo "Fixing: Restarting web container..."
        docker-compose -f docker-compose.prod.yml restart web
        sleep 3
    fi
fi
echo ""

echo "Step 6: Testing database connection..."
if docker-compose -f docker-compose.prod.yml exec -T web python manage.py check --database default > /dev/null 2>&1; then
    echo "✓ Database connection successful!"
else
    echo "✗ Database connection failed"
    echo ""
    echo "Trying to connect directly..."
    docker-compose -f docker-compose.prod.yml exec -T db psql -U studydeck_user -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1 && {
        echo "✓ Direct database connection works"
        echo "Issue might be with Django configuration"
    } || {
        echo "✗ Direct database connection also failed"
    }
fi
echo ""

echo "Step 7: Checking recent web container logs for errors..."
echo "Last 10 lines of web logs:"
docker-compose -f docker-compose.prod.yml logs web --tail=10
echo ""

echo "=========================================="
echo "Diagnostic Complete"
echo "=========================================="
echo ""
echo "If issues persist, try:"
echo "1. docker-compose -f docker-compose.prod.yml down"
echo "2. docker-compose -f docker-compose.prod.yml up -d --build"
echo "3. docker-compose -f docker-compose.prod.yml exec web python manage.py migrate"
echo ""
