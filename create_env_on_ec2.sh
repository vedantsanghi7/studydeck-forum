#!/bin/bash

# Helper script to create .env file on EC2 using values from local .env file
# Run this AFTER uploading your project to EC2
# Usage: ./create_env_on_ec2.sh your-key.pem ubuntu@your-ec2-ip

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 <path-to-key.pem> <user@ec2-ip>"
    echo "Example: $0 studydeck-key.pem ubuntu@54.123.45.67"
    exit 1
fi

KEY_FILE=$1
EC2_HOST=$2

# Check if local .env file exists
LOCAL_ENV=".env"
if [ ! -f "$LOCAL_ENV" ]; then
    echo "Error: Local .env file not found!"
    echo "Please make sure you're running this from the project directory with a .env file."
    exit 1
fi

echo "=========================================="
echo "Creating .env file on EC2 from local .env"
echo "=========================================="
echo ""

# Source the local .env file to get values
# We'll use grep/sed to safely extract values
SECRET_KEY=$(grep "^SECRET_KEY=" "$LOCAL_ENV" | cut -d '=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || echo "")
POSTGRES_DB=$(grep "^POSTGRES_DB=" "$LOCAL_ENV" | cut -d '=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || echo "studydeck_db")
POSTGRES_USER=$(grep "^POSTGRES_USER=" "$LOCAL_ENV" | cut -d '=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || echo "studydeck_user")
POSTGRES_PASSWORD=$(grep "^POSTGRES_PASSWORD=" "$LOCAL_ENV" | cut -d '=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || echo "")
EMAIL_BACKEND=$(grep "^EMAIL_BACKEND=" "$LOCAL_ENV" | cut -d '=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || echo "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST=$(grep "^EMAIL_HOST=" "$LOCAL_ENV" | cut -d '=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || echo "smtp.gmail.com")
EMAIL_PORT=$(grep "^EMAIL_PORT=" "$LOCAL_ENV" | cut -d '=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || echo "587")
EMAIL_USE_TLS=$(grep "^EMAIL_USE_TLS=" "$LOCAL_ENV" | cut -d '=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || echo "True")
EMAIL_HOST_USER=$(grep "^EMAIL_HOST_USER=" "$LOCAL_ENV" | cut -d '=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || echo "")
EMAIL_HOST_PASSWORD=$(grep "^EMAIL_HOST_PASSWORD=" "$LOCAL_ENV" | cut -d '=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || echo "")
DEFAULT_FROM_EMAIL=$(grep "^DEFAULT_FROM_EMAIL=" "$LOCAL_ENV" | cut -d '=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || echo "")
RATELIMIT_ENABLE=$(grep "^RATELIMIT_ENABLE=" "$LOCAL_ENV" | cut -d '=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || echo "True")
RATELIMIT_USE_CACHE=$(grep "^RATELIMIT_USE_CACHE=" "$LOCAL_ENV" | cut -d '=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || echo "default")

# If POSTGRES_PASSWORD is empty, extract from DATABASE_URL or generate one
if [ -z "$POSTGRES_PASSWORD" ]; then
    DATABASE_URL=$(grep "^DATABASE_URL=" "$LOCAL_ENV" | cut -d '=' -f2- | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' || echo "")
    if [ -n "$DATABASE_URL" ]; then
        # Extract password from DATABASE_URL (format: postgresql://user:password@host:port/db)
        POSTGRES_PASSWORD=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
    fi
    # If still empty, generate one
    if [ -z "$POSTGRES_PASSWORD" ]; then
        echo "Warning: POSTGRES_PASSWORD not found. Generating secure password..."
        POSTGRES_PASSWORD=$(openssl rand -base64 32 2>/dev/null || echo "change-this-password-$(date +%s)")
    fi
fi

# If SECRET_KEY is empty, generate one
if [ -z "$SECRET_KEY" ]; then
    echo "Warning: SECRET_KEY not found. Generating new one..."
    SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())" 2>/dev/null || echo "django-insecure-$(openssl rand -hex 32)")
fi

# Set defaults if empty
POSTGRES_DB=${POSTGRES_DB:-studydeck_db}
POSTGRES_USER=${POSTGRES_USER:-studydeck_user}
EMAIL_BACKEND=${EMAIL_BACKEND:-django.core.mail.backends.smtp.EmailBackend}
EMAIL_HOST=${EMAIL_HOST:-smtp.gmail.com}
EMAIL_PORT=${EMAIL_PORT:-587}
EMAIL_USE_TLS=${EMAIL_USE_TLS:-True}
RATELIMIT_ENABLE=${RATELIMIT_ENABLE:-True}
RATELIMIT_USE_CACHE=${RATELIMIT_USE_CACHE:-default}

# If DEFAULT_FROM_EMAIL is empty but EMAIL_HOST_USER exists, use that
if [ -z "$DEFAULT_FROM_EMAIL" ] && [ -n "$EMAIL_HOST_USER" ]; then
    DEFAULT_FROM_EMAIL="$EMAIL_HOST_USER"
fi

echo "Loaded from local .env file:"
echo "  SECRET_KEY: ${SECRET_KEY:0:30}..."
echo "  POSTGRES_DB: $POSTGRES_DB"
echo "  POSTGRES_USER: $POSTGRES_USER"
echo "  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:0:10}..."
echo "  EMAIL_HOST_USER: $EMAIL_HOST_USER"
echo ""

# Get EC2 public IP
echo "Getting EC2 public IP..."
EC2_IP=$(ssh -i "$KEY_FILE" "$EC2_HOST" "curl -s http://169.254.169.254/latest/meta-data/public-ipv4" 2>/dev/null || echo "your-ec2-ip")
echo "EC2 IP: $EC2_IP"
echo ""

# Prompt for domain
read -p "Enter your domain (e.g., forum.yourdomain.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    DOMAIN="forum.yourdomain.com"
    echo "Using default: $DOMAIN"
fi

echo ""
echo "Creating .env file on EC2..."

# Create a temporary file with the env content
TEMP_ENV=$(mktemp)
cat > "$TEMP_ENV" << EOF
# Django Settings
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$DOMAIN,$EC2_IP

# Database (REQUIRED for Docker Compose)
POSTGRES_DB=$POSTGRES_DB
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD

# Database URL (used by Django - updated for Docker)
DATABASE_URL=postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@db:5432/$POSTGRES_DB

# Email Configuration
EMAIL_BACKEND=$EMAIL_BACKEND
EMAIL_HOST=$EMAIL_HOST
EMAIL_PORT=$EMAIL_PORT
EMAIL_USE_TLS=$EMAIL_USE_TLS
EMAIL_HOST_USER=$EMAIL_HOST_USER
EMAIL_HOST_PASSWORD=$EMAIL_HOST_PASSWORD
DEFAULT_FROM_EMAIL=$DEFAULT_FROM_EMAIL

# Rate Limiting
RATELIMIT_ENABLE=$RATELIMIT_ENABLE
RATELIMIT_USE_CACHE=$RATELIMIT_USE_CACHE
EOF

# Upload the file to EC2
scp -i "$KEY_FILE" "$TEMP_ENV" "$EC2_HOST:~/studydeck/.env"

# Clean up
rm "$TEMP_ENV"

echo ""
echo "Verifying .env file was created..."
ssh -i "$KEY_FILE" "$EC2_HOST" "cd ~/studydeck && if [ -f .env ]; then echo '✓ .env file created successfully!'; echo ''; echo 'First few lines:'; head -10 .env; else echo '✗ .env file creation failed!'; fi"

echo ""
echo "=========================================="
echo "Done!"
echo "=========================================="
echo ""
echo "Note: Values were copied from your local .env file"
echo "Production-specific changes:"
echo "  - DEBUG set to False"
echo "  - ALLOWED_HOSTS updated with domain and EC2 IP"
echo "  - DATABASE_URL host changed from localhost to 'db' (Docker service name)"
echo ""
echo "Next steps:"
echo "1. SSH to EC2: ssh -i $KEY_FILE $EC2_HOST"
echo "2. Review .env: cd ~/studydeck && nano .env"
echo "3. Start Docker: docker-compose -f docker-compose.prod.yml up -d --build"
echo ""
