#!/bin/bash
# Development startup script with hot reload

echo "👨‍💻 Starting Local LLM Server in Development Mode..."

# Check if environment file exists
if [ ! -f .env ]; then
    echo "📋 Creating .env from .env.example..."
    cp .env.example .env
fi

# Create logs directory
mkdir -p logs

# Check Python version
uv python --version

# Install dependencies with uv
echo "📥 Installing dependencies with uv..."
uv sync

# Run tests
echo "🧪 Running tests..."
pytest tests/ -v --tb=short || true

# Start with hot reload
echo "🌐 Starting FastAPI server with hot reload..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

echo "✅ Development server is ready!"
