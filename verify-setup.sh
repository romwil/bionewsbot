#!/bin/bash

echo "BioNewsBot Docker Setup Verification"
echo "===================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
else
    echo "✅ Docker is installed: $(docker --version)"
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    exit 1
else
    echo "✅ Docker Compose is installed: $(docker-compose --version)"
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Creating from template..."
    cp .env.example .env
    echo "   Please edit .env with your configuration"
else
    echo "✅ .env file exists"
fi

# Check directory structure
echo ""
echo "Checking directory structure:"
for dir in frontend backend scheduler database redis nginx; do
    if [ -d "$dir" ]; then
        echo "✅ $dir/ directory exists"
    else
        echo "❌ $dir/ directory missing"
    fi
done

# Check key files
echo ""
echo "Checking key files:"
files=(
    "docker-compose.yml"
    "backend/Dockerfile"
    "backend/requirements.txt"
    "frontend/Dockerfile"
    "scheduler/Dockerfile"
    "scheduler/requirements.txt"
    "database/init.sql"
    "redis/redis.conf"
    "nginx/nginx.conf"
    "nginx/conf.d/bionewsbot.conf"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
    fi
done

echo ""
echo "Setup verification complete!"
echo ""
echo "To start the services, run:"
echo "  docker-compose up -d --build"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
