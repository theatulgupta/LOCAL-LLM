#!/bin/bash
# Main entry point script

echo "Local LLM Server - Quick Start"
echo "=============================="
echo ""
echo "Prerequisites:"
echo "- Ollama running on http://localhost:11434"
echo "- Python 3.11+ installed"
echo ""
echo "Quick commands:"
echo "1. Install dependencies: uv sync"
echo "2. Development server: uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo "3. Run tests: uv run pytest tests/ -v"
echo "4. Test with client: uv run python client.py"
echo ""
