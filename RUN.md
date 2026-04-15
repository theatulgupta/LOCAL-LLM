# 🚀 Run Instructions - Local LLM with RAG

Quick start guide to run the server on your friend's M4 MacBook and query from your M1.

---

## 📋 Prerequisites

- Both machines on same WiFi network
- Ollama installed with `qwen2.5-coder:7b` model
- Python 3.11+ (uv will handle this)
- Project cloned to both machines (or server side only)

### Verify Ollama is Ready

```bash
# Check if Ollama is installed
ollama --version

# Check if model is downloaded
ollama list
# Should show: qwen2.5-coder:7b

# If not downloaded yet
ollama pull qwen2.5-coder:7b
```

---

## 🖥️ **MACHINE 1: Friend's M4 MacBook (Server)**

### Step 1: Clone/Navigate to Project

```bash
# Option A: Clone from GitHub
git clone https://github.com/theatulgupta/LOCAL-LLM.git
cd LOCAL-LLM

# Option B: Use existing clone
cd /path/to/LOCAL-LLM
```

### Step 2: Install Dependencies (First Time Only)

```bash
uv sync
```

⏱️ Takes ~30 seconds to 2 minutes
✓ Creates `.venv` folder with all dependencies

### Step 3: Start Ollama (In a new terminal)

```bash
ollama serve
```

⏱️ Ollama will be listening on http://localhost:11434
✓ Keep this running in background

### Step 4: Start the FastAPI Server (In another terminal)

From the project directory:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Expected output:**

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

✅ **Server is now ready!** Keep both terminals open.

### Step 5: Find Your M4's IP Address

In another terminal on the M4:

```bash
ifconfig | grep "inet " | grep -v "127.0.0.1"
```

Look for: `inet 192.168.x.x` or `inet 10.x.x.x`
**Note this IP address** - you'll need it on your M1

Example output:

```
inet 192.168.1.45 netmask 0xffffff00 broadcast 192.168.1.255
```

So the IP is: **192.168.1.45**

---

## 💻 **MACHINE 2: Your M1 MacBook (Client)**

### Step 1: Test Connectivity

Replace `192.168.1.45` with friend's actual IP:

```bash
# Test health check
curl http://192.168.1.45:8000/api/health
```

✅ If you see a JSON response like this, you're connected:

```json
{ "status": "healthy", "version": "1.0.0", "ollama_status": "healthy" }
```

❌ If connection fails:

- Verify both machines are on same WiFi
- Check IP address is correct
- Try pinging: `ping 192.168.1.45`
- Check firewall on M4: System Preferences → Security & Privacy → Firewall

### Step 2: Clone Project (Optional - Only for Using Client Script)

```bash
# If you want to use Python client script
git clone https://github.com/theatulgupta/LOCAL-LLM.git
cd LOCAL-LLM
uv sync
```

### Step 3: Query the Server

#### **Option A: Using curl (Fastest)**

```bash
# Simple query
curl -X POST http://192.168.1.45:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain K-means clustering"}' \
  | python3 -m json.tool
```

#### **Option B: Using Python Client Script**

```bash
# Edit client.py and change BASE_URL to friend's IP
python3 client.py
```

#### **Option C: Stream Response (Real-time)**

```bash
curl -X POST http://192.168.1.45:8000/api/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is hierarchical clustering?"}' \
  | jq .
```

#### **Option D: Interactive Browser**

```bash
# Open API documentation in browser
open http://192.168.1.45:8000/docs
```

Click "Try it out" on any endpoint to test!

---

## 📚 Query Examples

### Basic Clustering Question

```bash
curl -X POST http://192.168.1.45:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain K-means clustering algorithm",
    "temperature": 0.7,
    "num_predict": 200
  }' | python3 -m json.tool
```

### Search Your Lab Notes

```bash
curl "http://192.168.1.45:8000/api/rag/search?query=k-means&top_k=3" \
  | python3 -m json.tool
```

### Check RAG Status

```bash
curl http://192.168.1.45:8000/api/rag/status \
  | python3 -m json.tool
```

**Expected response:**

```json
{
  "enabled": true,
  "ready": true,
  "indexed_files": 29,
  "indexed_chunks": 1847,
  "corpus_path": "/Users/theatulgupta/Desktop/Study Material/Sem II/Clustering/LAB"
}
```

---

## 🎓 Exam Mode (During Exam)

### On Friend's M4:

**Morning of exam, one time:**

```bash
cd /path/to/LOCAL-LLM
ollama serve &
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### On Your M1:

**During exam, as needed:**

```bash
# Quick answer
curl -X POST http://192.168.1.45:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Your question here"}'
```

✨ **Answer appears enriched with your lab notebook context!**

---

## 🔧 Troubleshooting

### "Connection refused" error

```bash
# Option 1: Verify IP address
ping 192.168.1.45

# Option 2: Check if server is running
curl http://192.168.1.45:8000/api/health

# Option 3: Check firewall on M4
# System Preferences → Security & Privacy → Firewall Options
# Add Python to allowed apps
```

### "No module named 'pydantic'" on friend's M4

```bash
cd /path/to/LOCAL-LLM
uv sync  # Reinstall dependencies
```

### Slow responses

```bash
# Check if Ollama is loaded
ollama list

# Check available memory on M4
top -l1 | grep "Memory:"

# Restart Ollama if needed
pkill ollama
ollama serve &
```

### RAG returns no results

```bash
# Force refresh the index
curl -X POST http://192.168.1.45:8000/api/rag/refresh
```

---

## 📊 Response Format

### Regular Query Response

```json
{
  "response": "K-means is a clustering algorithm...",
  "model": "qwen2.5-coder:7b",
  "prompt": "Explain K-means clustering",
  "rag": {
    "enabled": true,
    "sources_count": 3,
    "corpus_path": "/Users/theatulgupta/Desktop/Study Material/Sem II/Clustering/LAB",
    "indexed_files": 29,
    "indexed_chunks": 1847
  }
}
```

### Streaming Response (NDJSON format)

Each line is a JSON object:

```json
{"type":"rag_metadata","enabled":true,"sources_count":3}
{"type":"token","token":"K-means","model":"qwen2.5-coder:7b"}
{"type":"token","token":" is","model":"qwen2.5-coder:7b"}
...
```

---

## 🌐 API Endpoints Reference

| Endpoint           | Method | Purpose                      |
| ------------------ | ------ | ---------------------------- |
| `/api/health`      | GET    | Check server & Ollama status |
| `/api/models`      | GET    | List available models        |
| `/api/ask`         | POST   | Query LLM with RAG context   |
| `/api/ask/stream`  | POST   | Stream response tokens       |
| `/api/rag/status`  | GET    | Show indexing info           |
| `/api/rag/search`  | GET    | Search notebook corpus       |
| `/api/rag/refresh` | POST   | Reindex notebooks            |
| `/docs`            | GET    | Interactive API explorer     |

---

## ⏱️ Expected Performance

### M4 MacBook (Server)

- **Model loading**: 5-10 seconds (first query)
- **RAG indexing**: 2-3 seconds (first startup)
- **Response time**: 2-5 seconds typical
- **Concurrent users**: 8+ easily handled

### M1 MacBook (Client)

- **Network latency**: 100-300ms (WiFi local)
- **Total time**: 2.5-5.5 seconds per query
- **Memory used**: ~100MB (just for client)

---

## 📝 Useful Commands

```bash
# On M4 Server:
ollama list                          # See loaded models
ollama serve                         # Start Ollama
uv sync                              # Install dependencies
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000  # Start server

# On M1 Client:
curl http://192.168.x.x:8000/api/health              # Test connection
open http://192.168.x.x:8000/docs                    # Open API docs
python3 client.py                                     # Run test client

# Both:
ps aux | grep ollama                 # Check if Ollama running
ps aux | grep uvicorn                # Check if server running
lsof -i :8000                        # Check what's using port 8000
lsof -i :11434                       # Check what's using port 11434
```

---

## 🎯 Summary

**Server (M4) - Do Once:**

```bash
cd LOCAL-LLM && uv sync
ollama serve &
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Client (M1) - As Needed:**

```bash
curl -X POST http://<FRIEND-IP>:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Your question"}'
```

**That's it! Exam-ready.** ✅

---

For detailed documentation, see:

- `SETUP_INSTRUCTIONS.md` - Complete setup guide
- `IMPLEMENTATION_SUMMARY.md` - Technical details
- `DEPLOYMENT.md` - Production deployment options
- `README.md` - Project overview
