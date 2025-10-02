#!/bin/bash
# Script to force refresh Airflow DAGs và restart containers

echo "🔄 Force refreshing Airflow DAGs và restarting containers..."

# Stop containers
echo "⏹️ Stopping Airflow containers..."
docker-compose stop

# Remove DAG cache và compiled Python files
echo "🧹 Cleaning DAG cache..."
find logs/ -name "*.pyc" -delete 2>/dev/null || true
find dags/ -name "*.pyc" -delete 2>/dev/null || true
find dags/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Start containers
echo "🚀 Starting Airflow containers..."
docker-compose up -d

# Wait for webserver to be ready
echo "⏳ Waiting for Airflow webserver to be ready..."
sleep 45

# Check if webserver is running
echo "✅ Checking Airflow status..."
docker-compose ps

echo ""
echo "🌐 Airflow Web UI: http://localhost:8080"
echo "👤 Username: admin"  
echo "🔑 Password: admin"
echo ""
echo "📊 Check DAG status in web UI"
echo "🔍 Monitor logs: docker-compose logs -f airflow-webserver"