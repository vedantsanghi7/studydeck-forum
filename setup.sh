#!/bin/bash

# StudyDeck Forum Setup Script

echo "Setting up StudyDeck Forum..."

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run migrations
echo "Running migrations..."
python manage.py migrate

# Create superuser (interactive)
echo "Creating superuser..."
python manage.py createsuperuser

echo "Setup complete!"
echo "Run 'source venv/bin/activate' then 'python manage.py runserver' to start the development server."
