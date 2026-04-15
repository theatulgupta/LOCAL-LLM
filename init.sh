#!/bin/bash

# Make shell scripts executable
chmod +x start.sh dev.sh main.py client.py

echo "✅ Made scripts executable"
echo ""
echo "Project initialized! Next steps:"
echo ""
echo "1. Install Ollama from https://ollama.ai"
echo "2. Run: ollama run llama3"
echo "3. Create .env: cp .env.example .env"
echo "4. Install dependencies: make install"
echo "5. Start server: make dev"
echo ""
echo "Or use Docker:"
echo "  docker-compose up"
echo ""
