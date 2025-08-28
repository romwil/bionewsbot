#!/bin/bash

# BioNewsBot Frontend Setup Script

echo "🚀 Setting up BioNewsBot Frontend..."

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install Node.js and npm first."
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Create environment file if it doesn't exist
if [ ! -f .env.local ]; then
    echo "🔧 Creating environment file..."
    cat > .env.local << 'ENVEOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_APP_NAME=BioNewsBot
NEXT_PUBLIC_APP_VERSION=1.0.0
ENVEOF
    echo "✅ Environment file created"
else
    echo "ℹ️  Environment file already exists"
fi

# Build the application
echo "🏗️  Building the application..."
npm run build

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the development server:"
echo "  npm run dev"
echo ""
echo "To start the production server:"
echo "  npm start"
echo ""
echo "The application will be available at http://localhost:3000"
echo ""
echo "Make sure the backend API is running on http://localhost:8000"
