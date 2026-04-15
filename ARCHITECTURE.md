"""Architecture and design documentation"""

# Local LLM Server - Architecture Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Applications                       │
│  (Python, JavaScript, cURL, Mobile Apps, Web Browsers)      │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/HTTPS
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Server                            │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Request Handlers (Routes)                           │  │
│  │  - GET /api/health                                  │  │
│  │  - GET /api/models                                  │  │
│  │  - POST /api/ask                                    │  │
│  │  - POST /api/ask/stream                             │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Middleware Layer                                    │  │
│  │  - CORS & Security Headers                          │  │
│  │  - Rate Limiting                                     │  │
│  │  - Request/Response Logging                          │  │
│  │  - Error Handler                                     │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Service Layer                                       │  │
│  │  - OllamaService (LLM integration)                   │  │
│  │  - RateLimiter (Token bucket)                        │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Utilities                                           │  │
│  │  - Custom Exceptions                                │  │
│  │  - Logging Utilities                                │  │
│  │  - Configuration Management                          │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP REST API
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Ollama API Server (localhost:11434)             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  /api/generate   - Generate responses                │  │
│  │  /api/tags       - List available models             │  │
│  │  /api/pull       - Download models                   │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│           Local LLM Models (Memory/GPU)                      │
│  - llama3 (8B, 5GB)                                          │
│  - mistral (7B, 4GB)                                         │
│  - phi (2.7B, 1.5GB)                                         │
│  - And many others...                                        │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### Non-Streaming Request

```
1. Client sends prompt via POST /api/ask
2. FastAPI validates request with Pydantic model
3. Rate limiter checks client quota
4. OllamaService.generate() calls Ollama API
5. Ollama generates full response
6. FastAPI returns response to client
```

### Streaming Request

```
1. Client sends prompt via POST /api/ask/stream
2. FastAPI validates request
3. Rate limiter checks quota
4. OllamaService.generate() calls Ollama with stream=true
5. Response iterator yields tokens as they arrive
6. FastAPI returns StreamingResponse with NDJSON format
7. Client receives tokens in real-time
```

## Design Patterns Used

### 1. Dependency Injection

- FastAPI automatically injects dependencies via `Depends()`
- Services are singletons (created once, reused)
- Rate limiter injected as dependency

### 2. Service Layer Pattern

- `OllamaService` encapsulates all Ollama interactions
- Single responsibility principle
- Easy to mock for testing

### 3. Middleware Pattern

- Request/response logging
- CORS handling
- Rate limiting
- Error handling

### 4. Configuration Management

- Environment variables via `.env`
- Pydantic `BaseSettings` for validation
- Singleton pattern for settings

### 5. Exception Handling

- Custom exception classes for different error scenarios
- Proper HTTP status codes
- Structured error responses

## Error Handling Strategy

```
Request → Validation → Business Logic → JSON Response
            ↓              ↓              ↓
        422 Error     503 Error      200 Success
        (Client)      (Ollama)       (Response)
```

Error handling layers:

1. **Request Validation** - Pydantic models
2. **Business Logic** - Service layer exceptions
3. **Global Exception Handlers** - FastAPI handlers
4. **Logging** - Structured JSON logging

## Rate Limiting Algorithm

Token Bucket Implementation:

```
Each client gets a bucket with `N` tokens
Every `M` seconds, bucket refills

Request arrives:
  if tokens available:
    remove token
    allow request
  else:
    return 429 Too Many Requests
```

Configuration:

- Tokens per window: `RATE_LIMIT_REQUESTS` (default: 100)
- Window size: `RATE_LIMIT_WINDOW_SECONDS` (default: 60)

## Module Organization

```
app/
├── main.py              - App factory, middleware setup
├── config.py            - Settings & logging configuration
├── models.py            - Pydantic request/response models
├── routes/
│   └── llm.py          - API endpoint handlers
├── services/
│   └── ollama_service.py - Ollama integration
├── middleware/
│   └── rate_limit.py    - Rate limiting
└── utils/
    ├── exceptions.py    - Custom exceptions
    └── logger.py        - Logging utilities
```

## Configuration Management

Settings are loaded from `.env` file via Pydantic:

```python
class Settings(BaseSettings):
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    class Config:
        env_file = ".env"
```

## Performance Considerations

### 1. Connection Pooling

- Requests session reuses connections
- Retry strategy for failed requests

### 2. Async Processing

- FastAPI uses async functions for I/O
- Non-blocking request handling

### 3. Streaming Responses

- Efficient for large responses
- Lower memory usage
- Real-time feedback to client

### 4. Rate Limiting

- Prevents resource exhaustion
- Fair resource allocation
- Token bucket is O(1) operation

## Testing Strategy

### Unit Tests

- Test route handlers with mocked services
- Test Pydantic models
- Test exception handling

### Integration Tests

- Test with real Ollama server (optional)
- End-to-end request/response flow

### Coverage Goals

- Minimum 80% code coverage
- 100% for critical paths
- Test all error scenarios

## Deployment Architecture

### Development

```
Developer Machine
├── FastAPI (uvicorn)
└── Ollama (local)
```

### Production (Docker)

```
Docker Host
├── Container 1: FastAPI API Server
└── Container 2: Ollama Service

Connected via Docker Network
```

### Scale (Multiple Servers)

```
Load Balancer (nginx)
├── API Server 1 (FastAPI)
├── API Server 2 (FastAPI)
└── Ollama Server (shared)
```

## Security Considerations

1. **Input Validation** - Pydantic models
2. **Rate Limiting** - Prevent DoS attacks
3. **CORS Policy** - Configure allowed origins
4. **HTTPS** - Use reverse proxy with SSL
5. **Authentication** - JWT/OAuth2 (future)
6. **Logging** - Track all requests

## Technology Stack

- **Framework**: FastAPI (async web framework)
- **Server**: Uvicorn (ASGI server)
- **Validation**: Pydantic (data validation)
- **HTTP Client**: Requests (with retry logic)
- **Testing**: pytest (testing framework)
- **Containerization**: Docker & Docker Compose

## Future Enhancements

1. **Caching** - Redis for response caching
2. **Load Balancing** - Multiple Ollama instances
3. **Monitoring** - Prometheus metrics
4. **Authentication** - JWT tokens
5. **WebSockets** - Real-time chat
6. **Queue System** - Job queuing for long requests
