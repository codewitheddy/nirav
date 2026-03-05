#!/bin/bash

# Quick start script for local Docker development

echo "🚀 Starting Django Jewellery Site with Docker..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✅ Please edit .env file with your configuration before continuing."
    echo "   At minimum, generate a new SECRET_KEY:"
    echo "   python -c \"from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())\""
    exit 1
fi

# Build and start containers
echo "🔨 Building Docker containers..."
docker-compose up --build -d

# Wait for database
echo "⏳ Waiting for database to be ready..."
sleep 5

# Run migrations
echo "📦 Running database migrations..."
docker-compose exec web python manage.py migrate

# Create superuser (optional)
echo ""
echo "Would you like to create a superuser? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    docker-compose exec web python manage.py createsuperuser
fi

# Show logs
echo ""
echo "✅ Application is running!"
echo "🌐 Visit: http://localhost:8000"
echo "📊 Admin: http://localhost:8000/admin"
echo ""
echo "📝 View logs with: docker-compose logs -f"
echo "🛑 Stop with: docker-compose down"
echo ""
docker-compose logs -f
