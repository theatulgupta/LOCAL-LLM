# Deployment Guide

## Quick Start (Development)

### macOS / Linux

```bash
# Install dependencies
uv sync

# Ensure Ollama is running
ollama serve &

# Start server with auto-reload
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API will be available at `http://localhost:8000/docs`

## Production Deployment

### Option 1: Direct Server Installation (Simple)

#### macOS / Linux

```bash
# Clone and setup
cd /path/to/deployment
git clone <repo-url> .
uv sync

# Create startup script
cat > start-server.sh << 'EOF'
#!/bin/bash
cd /path/to/deployment
source .venv/bin/activate
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
EOF
chmod +x start-server.sh

# Run
./start-server.sh
```

#### Windows

```powershell
# Clone and setup
cd C:\path\to\deployment
git clone <repo-url> .
uv sync

# Run
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Option 2: Using systemd (Linux)

Create `/etc/systemd/system/local-llm.service`:

```ini
[Unit]
Description=Local LLM Server
After=network.target

[Service]
Type=simple
User=llm_user
WorkingDirectory=/path/to/Local LLM
ExecStart=/usr/bin/bash -c 'cd /path/to/Local\ LLM && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable local-llm
sudo systemctl start local-llm
sudo systemctl status local-llm
```

### Option 3: Using Gunicorn (Production Grade)

```bash
# Install gunicorn
uv pip install gunicorn

# Run with gunicorn
uv run gunicorn -w 4 -b 0.0.0.0:8000 --timeout 120 --access-logfile - app.main:app
```

## Network Setup for Exam Scenario

### Same WiFi Network Access

Your Mac → Friend's M4 MacBook Air (running the server)

1. **Find friend's IP address:**
   ```bash
   # On friend's Mac
   ifconfig | grep "inet "
   # Look for 192.168.x.x or 10.x.x.x address
   ```

2. **Start server on friend's machine:**
   ```bash
   cd /path/to/Local\ LLM
   uv sync
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

3. **Test from your Mac:**
   ```bash
   # Replace 192.168.X.X with friend's IP
   curl http://192.168.X.X:8000/api/health
   
   # Or use the client
   python client.py
   ```

4. **Update client configuration:**
   Edit `client.py` and change:
   ```python
   BASE_URL = "http://192.168.X.X:8000"
   ```

### Testing Connectivity

```bash
# Health check
curl http://friend-ip:8000/api/health

# List models
curl http://friend-ip:8000/api/models

# RAG status
curl http://friend-ip:8000/api/rag/status

# Make a query
curl -X POST http://friend-ip:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is clustering?"}'
```

## Configuration

### Environment Variables (.env)

```env
# Ollama Settings
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b
OLLAMA_TIMEOUT=300

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# RAG Settings
RAG_ENABLED=true
RAG_CORPUS_PATH=/Users/theatulgupta/Desktop/Study Material/Sem II/Clustering/LAB
RAG_TOP_K=3
RAG_MAX_CONTEXT_CHARS=7000

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/server.log
```

## Performance Tuning

### For M4 MacBook Air (24GB RAM)

- Use 4-8 workers: `--workers 8`
- Increase connection pool: modify `OllamaService._create_session()`
- Handle 10+ concurrent requests

### For M1 MacBook Air (8GB RAM)

- Use 2-4 workers: `--workers 2` or `--workers 4`
- Serve from localhost only or friendly network only
- Handle 3-5 concurrent requests safely
- Monitor with `top` or Activity Monitor

### Memory Optimization

```bash
# Monitor memory usage
top -l1 | grep "Memory:"

# Or use Activity Monitor on Mac
open -a Activity\ Monitor
```

## Monitoring & Logs

```bash
# View server logs
tail -f logs/server.log

# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check server health
watch -n 5 'curl http://localhost:8000/api/health'
```

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Ollama Connection Failed

```bash
# Ensure Ollama is running
ollama serve

# In another terminal, verify it's accessible
curl http://localhost:11434/api/tags

# Check what models are installed
ollama list
```

### RAG Index Not Working

```bash
# Check RAG status
curl http://localhost:8000/api/rag/status

# Force refresh RAG index
curl -X POST http://localhost:8000/api/rag/refresh

# Search the corpus
curl "http://localhost:8000/api/rag/search?query=clustering"
```

### Slow Responses

- Check available memory: `top` / Activity Monitor
- Check Ollama model is loaded: `ollama list`
- Reduce `num_predict` parameter in requests
- Use smaller model or wait for cache warming

## Backup & Restore

### Backup Configuration

```bash
# Backup .env and notebooks reference
cp .env .env.backup
cp -r /Users/theatulgupta/Desktop/Study\ Material backup/
```

### Restore

```bash
# Restore config
cp .env.backup .env

# Notebooks are on disk, no additional restore needed
```

## Security Notes

- This setup is designed for **local network only**
- Not recommended for internet exposure without authentication
- Add firewall rules to restrict access:
  ```bash
  # macOS firewall example
  sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setblockall off
  sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
  ```

## Support & Debugging

For issues, check:
1. Ollama connectivity: `curl http://localhost:11434/api/tags`
2. API health: `curl http://localhost:8000/api/health`
3. RAG status: `curl http://localhost:8000/api/rag/status`
4. Server logs: `logs/server.log`
5. Pydantic model validation: Pass `-v` to api startup for verbose output
