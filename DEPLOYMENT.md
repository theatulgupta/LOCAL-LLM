# Deployment Guide

## Pre-Deployment Checklist

- [ ] All tests pass: `make test`
- [ ] Code is formatted: `make format`
- [ ] No linting issues: `make lint`
- [ ] Environment variables configured in `.env`
- [ ] Ollama models downloaded
- [ ] Firewall rules updated
- [ ] CORS origins configured for production domain
- [ ] Secret management configured (if using authentication)

## Production Deployment Options

## Option 1: Linux Server (Recommended)

### 1. Server Setup

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.11+
sudo apt-get install python3.11 python3.11-venv python3.11-dev curl wget

# Create app directory
sudo mkdir -p /var/www/local-llm-server
cd /var/www/local-llm-server

# Clone repository
git clone <your-repo> .

# Set permissions
sudo chown -R $USER:$USER /var/www/local-llm-server
```

### 2. Ollama Setup

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Create systemd service
sudo nano /etc/systemd/system/ollama.service
```

```ini
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
Type=simple
User=ollama
Group=ollama
ExecStart=/usr/bin/ollama serve
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable ollama
sudo systemctl start ollama

# Verify
curl http://localhost:11434/api/tags
```

### 3. FastAPI Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create systemd service
sudo nano /etc/systemd/system/local-llm-api.service
```

```ini
[Unit]
Description=Local LLM API Server
After=network-online.target ollama.service
Wants=ollama.service

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/local-llm-server
Environment="PATH=/var/www/local-llm-server/venv/bin"
EnvironmentFile=/var/www/local-llm-server/.env
ExecStart=uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers=4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl enable local-llm-api
sudo systemctl start local-llm-api

# Check status
sudo systemctl status local-llm-api
```

### 4. Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt-get install nginx

# Create config
sudo nano /etc/nginx/sites-available/local-llm-server
```

```nginx
# Cache static responses
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m;

upstream local_llm_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;

    # Gzip compression
    gzip on;
    gzip_types application/json;

    location / {
        proxy_pass http://local_llm_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Streaming support
        proxy_buffering off;
        proxy_request_buffering off;

        # Timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /api/ask/stream {
        proxy_pass http://local_llm_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # Streaming specific
        proxy_buffering off;
        proxy_request_buffering off;
        chunked_transfer_encoding on;
    }

    # Cache non-streaming responses
    location /api/ask {
        proxy_pass http://local_llm_api;
        proxy_cache api_cache;
        proxy_cache_key "$scheme$request_method$host$request_uri$request_body";
        proxy_cache_valid 200 10m;
        add_header X-Cache-Status $upstream_cache_status;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/local-llm-server \
           /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### 5. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d api.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

---

## Option 2: Docker Deployment

### 1. Single Host Docker

```bash
# Build image
docker build -t local-llm-server:latest .

# Run with docker-compose
docker-compose up -d

# Check logs
docker-compose logs -f api
```

### 2. Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Create service
docker service create \
  --name local-llm-api \
  --publish 8000:8000 \
  --constraint node.role==manager \
  local-llm-server:latest

# Scale service
docker service scale local-llm-api=3
```

### 3. Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: local-llm-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: local-llm-api
  template:
    metadata:
      labels:
        app: local-llm-api
    spec:
      containers:
        - name: api
          image: local-llm-server:latest
          ports:
            - containerPort: 8000
          env:
            - name: OLLAMA_HOST
              value: "http://ollama-service:11434"
          resources:
            requests:
              memory: "2Gi"
              cpu: "1"
            limits:
              memory: "4Gi"
              cpu: "2"
          livenessProbe:
            httpGet:
              path: /api/health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: local-llm-api-service
spec:
  selector:
    app: local-llm-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

```bash
kubectl apply -f deployment.yaml
kubectl get pods
kubectl logs -f <pod-name>
```

---

## Production Configuration

### Environment Variables (.env)

```env
# API
API_HOST=127.0.0.1          # Only localhost for Nginx
API_PORT=8000
DEBUG=false

# Ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_TIMEOUT=300

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW_SECONDS=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/local-llm/server.log
```

### Monitoring & Logging

```bash
# Create log directory
sudo mkdir -p /var/log/local-llm
sudo chown www-data:www-data /var/log/local-llm

# Rotate logs
sudo nano /etc/logrotate.d/local-llm-server
```

```
/var/log/local-llm/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload local-llm-api > /dev/null 2>&1 || true
    endscript
}
```

### Monitoring with Prometheus (Optional)

```python
# Add to app/main.py
from prometheus_client import Counter, Histogram
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

request_count = Counter('api_requests_total', 'Total API requests')
request_duration = Histogram('api_request_duration_seconds', 'Request duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

---

## Performance Tuning

### Uvicorn Workers

```bash
# Production with 4 workers
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers=4
```

### System Limits

```bash
# Edit /etc/security/limits.conf
* soft nofile 65536
* hard nofile 65536
```

### Nginx Tuning

```nginx
# In /etc/nginx/nginx.conf
worker_processes auto;
worker_connections 4096;
```

---

## Health Monitoring

```bash
# Monitor API
watch -n 5 'curl -s http://localhost:8000/api/health | jq'

# Monitor Ollama
watch -n 5 'curl -s http://localhost:11434/api/tags | jq'

# Monitor system
htop
```

---

## Backup & Recovery

```bash
# Backup Ollama models
sudo tar -czf /backup/ollama-models.tar.gz ~/.ollama

# Backup application
sudo tar -czf /backup/local-llm-app.tar.gz /var/www/local-llm-server
```

---

## Troubleshooting Production

```bash
# Check service status
sudo systemctl status local-llm-api
sudo systemctl status ollama

# View logs
sudo journalctl -u local-llm-api -f
sudo journalctl -u ollama -f

# Test connectivity
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:11434/api/tags

# Restart services
sudo systemctl restart local-llm-api
sudo systemctl restart ollama
```

---

**For production support and advanced configurations, consult your DevOps team.**
