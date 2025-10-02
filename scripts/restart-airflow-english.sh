#!/bin/bash
# Script to restart Airflow with proper English locale configuration

echo "🔄 Restarting Airflow với cấu hình tiếng Anh..."

# Stop all Airflow services
echo "⏹️ Stopping Airflow services..."
docker-compose down

# Remove containers and volumes (optional - uncomment if needed)
# echo "🗑️ Cleaning up containers and volumes..."
# docker-compose down -v --remove-orphans

# Rebuild and restart services with new configuration
echo "🚀 Starting Airflow services với English locale..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service status
echo "✅ Checking service status..."
docker-compose ps

echo ""
echo "🌐 Airflow Webserver: http://localhost:8080"
echo "👤 Username: admin"
echo "🔑 Password: admin"
echo ""
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🌺 Flower (Celery): http://localhost:5555"
echo ""
echo "✨ Airflow GUI should now display in English!"
echo "🔄 If still in French, try clearing browser cache and cookies"