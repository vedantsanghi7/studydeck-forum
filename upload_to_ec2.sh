#!/bin/bash

# Script to upload local StudyDeck folder to EC2 and replace GitHub clone
# Usage: ./upload_to_ec2.sh your-key.pem ubuntu@your-ec2-ip

set -e

# Check if arguments are provided
if [ $# -lt 2 ]; then
    echo "Usage: $0 <path-to-key.pem> <user@ec2-ip>"
    echo "Example: $0 studydeck-key.pem ubuntu@54.123.45.67"
    exit 1
fi

KEY_FILE=$1
EC2_HOST=$2

# Check if key file exists
if [ ! -f "$KEY_FILE" ]; then
    echo "Error: Key file '$KEY_FILE' not found!"
    exit 1
fi

# Check if key file has correct permissions
if [ "$(stat -f '%A' "$KEY_FILE" 2>/dev/null || stat -c '%a' "$KEY_FILE" 2>/dev/null)" != "400" ]; then
    echo "Setting key file permissions to 400..."
    chmod 400 "$KEY_FILE"
fi

echo "=========================================="
echo "Uploading StudyDeck to EC2"
echo "=========================================="
echo "Key file: $KEY_FILE"
echo "EC2 host: $EC2_HOST"
echo ""

# Get the project directory name
PROJECT_DIR=$(basename "$(pwd)")

echo "Step 1: Removing old GitHub clone on EC2..."
ssh -i "$KEY_FILE" "$EC2_HOST" "rm -rf ~/$PROJECT_DIR 2>/dev/null || true"

echo "Step 2: Creating project directory on EC2..."
ssh -i "$KEY_FILE" "$EC2_HOST" "mkdir -p ~/$PROJECT_DIR"

echo "Step 3: Uploading files (this may take a few minutes)..."
# Use rsync if available, otherwise use scp
if command -v rsync &> /dev/null; then
    rsync -avz --progress \
        -e "ssh -i $KEY_FILE" \
        --exclude 'venv/' \
        --exclude '__pycache__/' \
        --exclude '*.pyc' \
        --exclude '.git/' \
        --exclude 'db.sqlite3' \
        --exclude 'staticfiles/' \
        --exclude 'media/' \
        --exclude '.env' \
        --exclude '.env.local' \
        --exclude '.DS_Store' \
        ./ "$EC2_HOST:~/$PROJECT_DIR/"
else
    echo "rsync not found, using scp (slower)..."
    scp -i "$KEY_FILE" -r \
        --exclude='venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.git' \
        --exclude='db.sqlite3' \
        --exclude='staticfiles' \
        --exclude='media' \
        --exclude='.env' \
        ./ "$EC2_HOST:~/$PROJECT_DIR/"
fi

echo ""
echo "Step 4: Verifying Docker files were uploaded..."
ssh -i "$KEY_FILE" "$EC2_HOST" "cd ~/$PROJECT_DIR && ls -la Dockerfile docker-compose.yml docker-compose.prod.yml nginx.conf 2>/dev/null && echo '✓ All Docker files found!' || echo '✗ Some Docker files missing!'"

echo ""
echo "=========================================="
echo "Upload complete!"
echo "=========================================="
echo ""
echo "Next steps on EC2:"
echo "1. SSH to EC2: ssh -i $KEY_FILE $EC2_HOST"
echo "2. Navigate: cd ~/$PROJECT_DIR"
echo "3. Create .env file (see Step 4 reminder above or AWS_DEPLOYMENT.md Step 4)"
echo "4. Run: docker-compose -f docker-compose.prod.yml up -d --build"
echo ""
