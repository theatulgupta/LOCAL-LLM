# Local LLM Server with RAG - Setup & User Guide

## 🎯 What is This?

A **fully offline** Local LLM server with RAG (Retrieval-Augmented Generation) that:

- Runs on local machines (M1/M4 MacBooks)
- Answers questions enriched with your lab notebooks
- Works across your WiFi network for exam scenarios
- Requires NO internet connection

## 📋 Current Setup Status

### ✅ Completed

- ✅ FastAPI server application with async streams
- ✅ Ollama integration with qwen2.5-coder:7b model
- ✅ RAG service indexing 29 notebooks from your LAB folder
- ✅ Fixed streaming response parsing
- ✅ RAG context injection in /api/ask endpoints
- ✅ New RAG-specific endpoints (/api/rag/search, /api/rag/status)
- ✅ Rate limiting (100 req/min per IP)
- ✅ Comprehensive error handling & logging
- ✅ Request/response validation with Pydantic

### 📦 Dependencies to Install

All specified in `pyproject.toml`:

- fastapi, uvicorn, requests, pydantic, pydantic-settings
- pytest, pytest-asyncio, httpx (for testing)
- python-json-logger, python-dotenv

## 🚀 Quick Start

### Step 1: On Friend's M4 MacBook Air (Server)

```bash
# Go to project directory
cd "/Users/theatulgupta/Desktop/Local LLM"

# Install all dependencies (first time only)
uv sync

# Make sure Ollama is running in another terminal
ollama serve &

# Start the API server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Output should show:

```
Uvicorn running on http://0.0.0.0:8000
```

### Step 2: On Your M1 MacBook (Client)

```bash
# Find friend's IP on the network
ifconfig | grep "inet "  # Look for 192.168.x.x or 10.x.x.x

# Test connectivity from your machine
curl http://<friend-ip>:8000/api/health

# Should return: {"status":"healthy","version":"1.0.0",...}
```

## 📚 Lab Notebook Setup

**Automatically handled!** The system indexes:

- **Location**: `/Users/theatulgupta/Desktop/Study Material/Sem II/Clustering/LAB`
- **Format**: Jupyter notebooks (.ipynb)
- **Notebooks Found**: 29 files
- **Content**: Code, markdown, outputs all indexed for RAG

### Example Notebooks Indexed:

- `25MCSS06_ASSIGNMENT_LAB_8.ipynb` (10 cells)
- `25MCSS06_LAB_TEST.ipynb`
- `25MCSS06_ASSIGNMENT_LAB_9.ipynb`

## 🔌 API Endpoints

### Health & Status

```bash
# Check if server is healthy
curl http://localhost:8000/api/health

# List available Ollama models
curl http://localhost:8000/api/models

# Get RAG indexing status
curl http://localhost:8000/api/rag/status
```

### Querying with RAG Context (Exam Mode)

Best for exam prep - answers enriched with your notes:

```bash
# Simple query (returns full response)
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain the K-means clustering algorithm",
    "model": "qwen2.5-coder:7b",
    "temperature": 0.7
  }'

# Stream response (real-time tokens)
curl -X POST http://localhost:8000/api/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is hierarchical clustering?"}'
```

### RAG-Specific Endpoints

```bash
# Search your notebook corpus
curl "http://localhost:8000/api/rag/search?query=k-means&top_k=3"

# Refresh RAG index (if you add new notebooks)
curl -X POST http://localhost:8000/api/rag/refresh
```

## 📊 Response Format

### Regular Query Response

```json
{
  "response": "K-means is a clustering algorithm...",
  "model": "qwen2.5-coder:7b",
  "prompt": "Explain K-means",
  "rag": {
    "enabled": true,
    "sources_count": 2,
    "corpus_path": "/Users/theatulgupta/Desktop/Study Material/Sem II/Clustering/LAB",
    "indexed_files": 29,
    "indexed_chunks": 1847
  }
}
```

### Streaming Response (NDJSON)

Each line is a JSON object:

```
{"type":"rag_metadata","enabled":true,"sources_count":2,"corpus_path":"/Users/..."}
{"type":"token","token":"K-means","model":"qwen2.5-coder:7b"}
{"type":"token","token":" is","model":"qwen2.5-coder:7b"}
...
```

## 🧪 Testing

### Run Comprehensive Tests

```bash
cd "/Users/theatulgupta/Desktop/Local LLM"
python3 test_setup.py
```

Tests check:

- Ollama connectivity
- RAG corpus availability (29 notebooks)
- Module imports
- Pydantic models
- Notebook parsing
- RAG service functionality

### Use the Python Client

```bash
# Edit client.py to update BASE_URL to friend's IP
python3 client.py
```

### Manual Testing with curl

```bash
# Health check
curl http://localhost:8000/api/health

# Simple query
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt":"What is clustering?"}'

# Stream example
curl -X POST http://localhost:8000/api/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Explain K-means clustering"}' \
  | jq . # pipe to jq for pretty-print if available
```

## 📊 Configuration

### Default Settings (in `app/config.py`)

```python
# Ollama
ollama_host = "http://localhost:11434"
ollama_model = "qwen2.5-coder:7b"  # Default model
ollama_timeout = 300  # 5 minutes

# RAG
rag_enabled = True
rag_corpus_path = "/Users/theatulgupta/Desktop/Study Material/Sem II/Clustering/LAB"
rag_top_k = 3  # Top 3 chunks per query
rag_chunk_size = 120  # Words per chunk
rag_max_context_chars = 7000  # Max context length

# Rate Limiting
rate_limit_requests = 100  # per minute
rate_limit_window_seconds = 60

# API
api_port = 8000
api_host = "0.0.0.0"  # Accessible from network
```

## 🔍 How RAG Works

1. **Indexing**: On startup, RAG service scans all `.ipynb` files
2. **Chunking**: Each notebook is split into 120-word chunks
3. **Search**: For each query, finds top-3 matching chunks
4. **Injection**: Appends context to prompt before Ollama
5. **Response**: LLM answers with context from your notes

### Example RAG Flow:

```
Your Query: "What is K-means?"
         ↓
RAG Search finds: (from ASSIGNMENT_LAB_8.ipynb)
  "K-means clustering is a partitioning algorithm..."
  "The algorithm minimizes within-cluster variance..."
  "Centroid initialization affects convergence..."
         ↓
Enhanced Prompt:
"Use this context from your lab notes:
[3 chunks from notebooks]

Question: What is K-means?"
         ↓
Ollama generates answer using both context + knowledge
```

## ⚠️ Important Notes

### Network

- Both machines must be on **same WiFi network**
- Friend's IP must be accessible from your machine
- Firewall may need adjustment (macOS: System Preferences → Security & Privacy → Firewall)

### Performance

- **M4 with 24GB**: Can handle 8+ concurrent users
- **M1 with 8GB**: Recommended 3-5 concurrent requests
- Responses typically: 2-5 seconds depending on model load

### Model Details

- **Model**: `qwen2.5-coder:7b`
- **Size**: 4.7 GB
- **Optimized for**: Code, technical questions (perfect for CS labs!)
- **Context Window**: 32k tokens

## 🛠️ Troubleshooting

### Ollama Not Running

```bash
# Check if running
ps aux | grep ollama

# Start it
ollama serve

# List models
ollama list
```

### Port 8000 Already in Use

```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Can't Connect from Friend's Machine IP

```bash
# From your machine, test ping
ping <friend-ip>

# Try localhost first from friend's machine
curl http://localhost:8000/api/health

# Check if server is actually listening
netstat -tuln | grep 8000
```

### Slow Responses

- Check memory on friend's machine: `top` or Activity Monitor
- Check if Ollama is loaded: `ollama list` (should show model loaded)
- Reduce `num_predict` parameter in requests (default: 128)
- Restart Ollama service

### RAG Returns No Results

```bash
# Check RAG status
curl http://localhost:8000/api/rag/status

# Force refresh
curl -X POST http://localhost:8000/api/rag/refresh

# Search with simple query
curl "http://localhost:8000/api/rag/search?query=algorithm"
```

## 📂 Project Structure

```
Local LLM/
├── app/
│   ├── main.py              # FastAPI app factory
│   ├── config.py            # Settings (RAG path, model, etc.)
│   ├── models.py            # Pydantic request/response models
│   ├── routes/
│   │   └── llm.py           # All API endpoints
│   ├── services/
│   │   ├── ollama_service.py    # Ollama API integration
│   │   └── rag_service.py       # Notebook RAG system
│   ├── middleware/
│   │   └── rate_limit.py    # Rate limiting
│   └── utils/
│       ├── logger.py        # Request logging
│       └── exceptions.py     # Custom exceptions
├── tests/
│   └── test_routes.py       # Integration tests
├── pyproject.toml           # Dependencies (uv)
├── README.md                # Project overview
├── QUICKSTART.md            # Getting started
├── DEPLOYMENT.md            # Deployment guide
├── ARCHITECTURE.md          # System design
├── client.py                # Python test client
├── test_setup.py            # Setup validation tests
└── logs/                    # Server logs

RAG Corpus:
/Users/theatulgupta/Desktop/Study Material/Sem II/Clustering/LAB/
├── 25MCSS06_ASSIGNMENT_LAB_8.ipynb
├── 25MCSS06_LAB_TEST.ipynb
├── 25MCSS06_ASSIGNMENT_LAB_9.ipynb
└── ...26 more notebooks
```

## 🎓 Exam Mode Workflow

During exams with this setup:

1. **Before Exam**: Friend starts server on M4 (takes ~10 sec)

   ```bash
   cd "/Users/theatulgupta/Desktop/Local LLM"
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

2. **During Exam**: You query from M1 with your client

   ```bash
   python3 client.py
   # Or use curl: curl -X POST http://<friend-ip>:8000/api/ask ...
   ```

3. **Get Answers**: Enriched with your lab notebook context
   - Code explanations from your assignments
   - Algorithm details from test notes
   - Examples from your lab work

## 📈 Next Steps

1. **Test Locally First**

   ```bash
   cd "/Users/theatulgupta/Desktop/Local LLM"
   uv sync
   python3 test_setup.py  # Should show 6/6 passing
   ```

2. **Run Development Server**

   ```bash
   ollama serve &
   uv run uvicorn app.main:app --reload
   # Visit http://localhost:8000/docs for interactive API explorer
   ```

3. **Deploy to Friend's M4**
   - Transfer project folder
   - Run same `uv sync`
   - Start with `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - Stay on for exam duration

## 💬 Support

If something breaks:

1. Check `logs/server.log` for errors
2. Run `python3 test_setup.py` to diagnose
3. Verify Ollama is running: `ollama list`
4. Check network connectivity: `ping 192.168.x.x`
5. Review API docs: `http://localhost:8000/docs`

---

**Ready to ace your exams with AI + your own notes! 🚀**
