#!/bin/bash

# Script to SSH into EC2 and diagnose/fix database issues
# Usage: ./diagnose_and_fix_db.sh <key-file> <user@ec2-ip>

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 <path-to-key.pem> <user@ec2-ip>"
    echo "Example: $0 studydeck-key.pem ubuntu@54.123.45.67"
    exit 1
fi

KEY_FILE=$1
EC2_HOST=$2

echo "=========================================="
echo "Connecting to EC2 to diagnose database..."
echo "=========================================="
echo ""

# Upload the fix script to EC2
echo "Step 1: Uploading diagnostic script to EC2..."
scp -i "$KEY_FILE" fix_db_on_ec2.sh "$EC2_HOST:~/studydeck/"

# Make it executable
ssh -i "$KEY_FILE" "$EC2_HOST" "chmod +x ~/studydeck/fix_db_on_ec2.sh"

echo "Step 2: Running diagnostic script on EC2..."
echo ""

# Run the diagnostic script
ssh -i "$KEY_FILE" "$EC2_HOST" "cd ~/studydeck && ./fix_db_on_ec2.sh"

echo ""
echo "=========================================="
echo "Done! Check the output above."
echo "=========================================="
echo ""
