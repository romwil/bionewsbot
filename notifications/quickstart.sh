#!/bin/bash

# BioNewsBot Notification Service Quick Start Script

echo "🚀 BioNewsBot Notification Service Quick Start"
echo "============================================="
echo ""

# Check Python version
echo "📌 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ is required. Found: $python_version"
    exit 1
fi
echo "✅ Python $python_version"

# Check for Redis
echo ""
echo "📌 Checking for Redis..."
if command -v redis-cli &> /dev/null; then
    echo "✅ Redis is installed"
else
    echo "❌ Redis is not installed. Please install Redis first."
    echo "   Ubuntu/Debian: sudo apt-get install redis-server"
    echo "   MacOS: brew install redis"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "📌 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo ""
echo "📌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📌 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Dependencies installed"

# Check for .env file
echo ""
echo "📌 Checking configuration..."
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "✅ Created .env file from template"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file with your Slack credentials:"
    echo "   1. SLACK_BOT_TOKEN (starts with xoxb-)"
    echo "   2. SLACK_APP_TOKEN (starts with xapp-)"
    echo "   3. SLACK_SIGNING_SECRET"
    echo ""
    echo "   Get these from your Slack app at: https://api.slack.com/apps"
    echo ""
    read -p "Press Enter after updating .env file to continue..."
fi

# Start Redis if not running
echo ""
echo "📌 Starting Redis..."
if ! pgrep -x "redis-server" > /dev/null; then
    redis-server --daemonize yes
    echo "✅ Redis started"
else
    echo "✅ Redis is already running"
fi

# Database setup reminder
echo ""
echo "📌 Database Setup"
echo "⚠️  Make sure you have created the notification_history table in your database."
echo "   See README.md for the SQL schema."
echo ""

# Start the service
echo "🎉 Starting BioNewsBot Notification Service..."
echo ""
echo "Service will be available at:"
echo "  - API: http://localhost:8001"
echo "  - Health: http://localhost:8001/webhooks/health"
echo "  - Metrics: http://localhost:8001/webhooks/metrics"
echo ""
echo "Press Ctrl+C to stop the service"
echo ""

# Run the service
python -m uvicorn main:app --reload --port 8001
