# Quick Start Guide

## ⚡ 5-Minute Setup

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) installed
- bash/zsh terminal

### Installation

```bash
# 1. Clone and enter directory
cd "Local LLM"

# 2. Setup Python environment with uv
make install

# 3. Copy configuration
cp .env.example .env

# 4. Run Ollama (if not already running)
ollama serve

# 5. In another terminal, start FastAPI development server
make dev
```

## 🚀 Start Using

Once server is running at `http://localhost:8000`:

### Swagger UI (Interactive Docs)

```
Open browser: http://localhost:8000/docs
```

### Test Health

```bash
curl http://localhost:8000/api/health
```

### Ask a Question

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is machine learning?"}'
```

### Using Python Client

```bash
python client.py "What is artificial intelligence?"
python client.py --stream "Write a poem about cats"
python client.py --check-health
python client.py --list-models
```

## 📊 Development Workflow

### Run Tests

```bash
make test
make test-cov  # With coverage
```

### Code Formatting

```bash
make format    # Auto-format code
make lint      # Check code quality
```

### Stop Everything

```bash
# Kill FastAPI
Ctrl+C

# Kill Ollama (in separate terminal)
Ctrl+C
```

## � Useful Commands

```bash
make help              # Show all available commands
make dev               # Start with hot reload
make prod              # Start production server
make test              # Run tests
make format            # Format code
make clean             # Clean cache/build files
```

## 🔧 Useful Commands

```bash
make help              # Show all available commands
make dev               # Start with hot reload
make prod              # Start production server
make test              # Run tests
make format            # Format code
make docker-up         # Start Docker containers
make docker-down       # Stop containers
make clean             # Clean cache/build files
```

## 📚 API Endpoints

```bash
# Health check
GET /api/health

# List models
GET /api/models

# Non-streaming query
POST /api/ask
{"prompt": "Your question", "model": "llama3"}

# Streaming query
POST /api/ask/stream
{"prompt": "Your question", "stream": true}

# Interactive docs
GET /docs       # Swagger UI
GET /redoc      # ReDoc
```

## 🧪 Test the Server

```bash
# Using curl
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is Python?"}'

# Using Python
python client.py "What is Python?"

# Using JavaScript/Node
fetch('http://localhost:8000/api/ask', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ prompt: 'What is Python?' })
}).then(r => r.json()).then(d => console.log(d.response))
```

## ⚠️ Troubleshooting

### "Connection refused" error?

```bash
# Make sure Ollama is running
ollama serve
# or in another terminal
ollama run llama3
```

### "Port 8000 already in use"?

```bash
# Change port in .env
API_PORT=8001

# Or kill existing process
lsof -i :8000
kill -9 <PID>
```

### Low performance?

```bash
# Check your model size
ollama list

# Use a smaller model
ollama run mistral    # Faster than llama3

# Reduce prediction tokens
# In request: "num_predict": 128
```

## 📖 Full Documentation

- [README.md](README.md) - Complete documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [docs link](http://localhost:8000/docs) - Interactive API docs

## 🎓 Interview Prep

**30 second pitch:**

> "I built a production-grade LLM inference server using FastAPI and Ollama. The system includes RESTful API endpoints, request validation with Pydantic, rate limiting with token bucket algorithm, structured logging, and comprehensive error handling. It supports both streaming and non-streaming responses and is deployable via Docker."

**Key points to mention:**

- ✅ FastAPI for async performance
- ✅ Ollama for local LLM inference
- ✅ Rate limiting & error handling
- ✅ Streaming support for real-time responses
- ✅ Docker containerization
- ✅ Comprehensive tests & logging
- ✅ Production-ready error handling

---

**Happy coding! 🚀**
