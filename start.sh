#!/bin/bash

echo "🚀 Starting SDB Worker Project with Docker Compose..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it first."
    exit 1
fi

echo "📦 Building and starting services..."
docker-compose up --build


echo "✅ Services started successfully!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend: http://localhost:8000"
echo "🗄️  Database: localhost:5432"
echo ""
echo "Press Ctrl+C to stop services"
