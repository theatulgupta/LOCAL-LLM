#!/bin/bash
# Production startup script

set -e

echo "🚀 Starting Local LLM Server..."

# Check if environment file exists
if [ ! -f .env ]; then
    echo "📋 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env created. Please review and update if needed."
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Install/upgrade dependencies with uv
echo "📥 Installing dependencies with uv..."
uv sync

# Run database migrations (if applicable)
# python -m alembic upgrade head

# Start the server
echo "🌐 Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

echo "✅ Server is ready!"
