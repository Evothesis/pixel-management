#!/bin/bash

# Development Environment Setup Script
# Sets up the complete pixel management development environment

set -e

echo "🚀 Setting up Pixel Management Development Environment"
echo "=================================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Step 1: Download geolocation data
echo "📥 Step 1: Downloading geolocation data..."
./scripts/download-geolocation-data.sh

echo ""

# Step 2: Start PostgreSQL database
echo "🐘 Step 2: Starting PostgreSQL database..."
docker compose --env-file .env.development --profile database up -d

echo "⏳ Waiting for PostgreSQL to be ready..."
timeout=60
while [ $timeout -gt 0 ]; do
    if docker compose --env-file .env.development exec postgres pg_isready -U pixeluser -d pixeldb >/dev/null 2>&1; then
        echo "✅ PostgreSQL is ready!"
        break
    fi
    sleep 2
    timeout=$((timeout - 2))
done

if [ $timeout -le 0 ]; then
    echo "❌ PostgreSQL failed to start within 60 seconds"
    exit 1
fi

echo ""

# Step 3: Initialize database with geolocation data
echo "🗄️  Step 3: Initializing database with geolocation data..."
if docker compose --env-file .env.development run --rm postgres-init; then
    echo "✅ Database initialized successfully!"
else
    echo "⚠️  Database initialization failed or data already exists"
fi

echo ""

# Step 4: Start all services
echo "🌟 Step 4: Starting all services..."
docker compose --env-file .env.development --profile database --profile backend --profile frontend up -d

echo ""
echo "🎉 Development environment is ready!"
echo "=================================="
echo "🌐 Frontend:  http://localhost:3000"
echo "🔧 Backend:   http://localhost:8000"
echo "📊 API Docs:  http://localhost:8000/docs"
echo "🐘 Database:  localhost:5432"
echo ""
echo "💡 Useful commands:"
echo "   View logs:    docker compose --env-file .env.development logs -f"
echo "   Stop all:     docker compose --env-file .env.development down"
echo "   Restart:      docker compose --env-file .env.development restart"
echo ""
echo "📁 Data location: ./data/geolocation/"