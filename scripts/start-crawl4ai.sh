#!/bin/bash
# Script to start Crawl4AI service for AI-powered web scraping

echo "🤖 Starting Crawl4AI Service for AI extraction..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create .env file with API keys."
    echo "💡 Copy .env.example to .env and add your real API keys."
    exit 1
fi

# Start only Crawl4AI service
echo "🚀 Starting Crawl4AI container..."
docker-compose up crawl4ai -d

# Wait for service to be ready
echo "⏳ Waiting for Crawl4AI to be ready..."
sleep 10

# Check if service is running
echo "✅ Checking service status..."
docker-compose ps crawl4ai

# Test the service
echo "🧪 Testing Crawl4AI connection..."
python utils/test_crawl4ai.py

echo ""
echo "🎯 Crawl4AI Service Info:"
echo "🌐 URL: http://localhost:11235"
echo "📊 Health: http://localhost:11235/health"
echo "🤖 AI Model: Gemini 2.5 Flash"
echo ""
echo "✅ Ready for AI-powered hotel details extraction!"