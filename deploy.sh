#!/bin/bash
# Deployment script for AWS EC2

set -e

echo "Starting deployment..."

# Pull latest code
echo "Pulling latest code..."
git pull origin main

# Build and restart containers
echo "Building and restarting containers..."
docker-compose -f docker-compose.prod.yml up -d --build

# Run migrations
echo "Running migrations..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
docker-compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

# Restart web service
echo "Restarting web service..."
docker-compose -f docker-compose.prod.yml restart web

echo "Deployment complete!"
echo "Check logs with: docker-compose -f docker-compose.prod.yml logs -f"
