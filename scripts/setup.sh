#!/bin/bash

echo "🚀 Setting up EmpathAI Chatbot..."

# Create necessary directories
mkdir -p data/faiss_index data/backups logs
mkdir -p docker/postgres

# Copy environment file if not exists
if [ ! -f .env ]; then
    echo "📝 Copying .env.example to .env"
    cp .env.example .env
    echo "⚠️  Please update .env with your Gemini API key!"
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Start services with Docker Compose
echo "🐳 Starting PostgreSQL and Redis..."
docker-compose up -d postgres redis

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Initialize database
echo "🗄️  Initializing database..."
docker-compose run --rm app python -c "
from app.database.postgres import init_database
init_database()
"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "1. Add your Gemini API key to .env"
echo "2. Run: docker-compose up app"
echo "3. Open: http://localhost:8000"
echo ""
echo "For testing:"
echo "Run: python -m pytest tests/"