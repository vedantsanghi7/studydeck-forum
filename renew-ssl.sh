#!/bin/bash

# SSL Certificate Auto-Renewal Script
# This script renews Let's Encrypt certificates and restarts nginx

set -e

cd ~/studydeck

# Renew certificates (webroot mode - doesn't need to stop nginx)
sudo certbot renew --quiet --webroot -w /var/www/certbot

# Check if renewal was successful and restart nginx
if [ $? -eq 0 ]; then
    echo "Certificate renewal successful. Restarting nginx..."
    docker-compose -f docker-compose.prod.yml restart nginx
    echo "✓ SSL certificate renewed and nginx restarted"
else
    echo "✗ Certificate renewal failed"
    exit 1
fi
