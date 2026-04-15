"""FastAPI routes for LLM endpoints"""

import logging
import time
import json
from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import StreamingResponse

from app.models import (
    QueryRequest,
    QueryResponse,
    HealthResponse,
    ErrorResponse,
    AvailableModelsResponse,
    StreamingQueryResponse
)
from app.services.ollama_service import get_ollama_service
from app.middleware.rate_limit import get_rate_limiter
from app.utils.exceptions import (
    OllamaConnectionError,
    InvalidPromptError,
    OllamaError,
    RateLimitExceededError
)
from app.utils.logger import log_request, log_response
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["LLM"])


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    if request.client:
        return request.client.host
    return "unknown"


def apply_rate_limit(request: Request) -> str:
    """Rate limit dependency"""
    client_ip = get_client_ip(request)
    rate_limiter = get_rate_limiter()
    rate_limiter.is_allowed(client_ip)
    return client_ip


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """Health check endpoint"""
    start_time = time.time()
    client_ip = get_client_ip(request)
    log_request(logger, "GET", "/api/health", client_ip)

    try:
        ollama_service = get_ollama_service()
        is_healthy = ollama_service.health_check()

        ollama_status = "healthy" if is_healthy else "unhealthy"

        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            ollama_status=ollama_status
        )

        duration = (time.time() - start_time) * 1000
        log_response(logger, "GET", "/api/health", 200, duration)

        return response
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        duration = (time.time() - start_time) * 1000
        log_response(logger, "GET", "/api/health", 500, duration)
        raise


@router.get("/models", response_model=AvailableModelsResponse)
async def list_models(request: Request, client_ip: str = Depends(apply_rate_limit)):
    """List available models"""
    start_time = time.time()
    log_request(logger, "GET", "/api/models", client_ip)

    try:
        ollama_service = get_ollama_service()
        models = ollama_service.list_models()

        response = AvailableModelsResponse(
            models=models,
            count=len(models)
        )

        duration = (time.time() - start_time) * 1000
        log_response(logger, "GET", "/api/models", 200, duration)

        return response
    except OllamaConnectionError as e:
        logger.error(f"Failed to list models: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing models: {e}")
        raise OllamaError(f"Failed to list models: {str(e)}")


@router.post("/ask", response_model=QueryResponse)
async def ask_llm(
    query: QueryRequest,
    request: Request,
    client_ip: str = Depends(apply_rate_limit)
):
    """
    Send a query to the LLM

    Returns the generated response from the model.
    """
    start_time = time.time()
    log_request(logger, "POST", "/api/ask", client_ip)

    try:
        ollama_service = get_ollama_service()

        logger.debug(f"Processing query from {client_ip}: {query.prompt[:50]}...")

        result = ollama_service.generate(
            prompt=query.prompt,
            model=query.model,
            temperature=query.temperature,
            top_p=query.top_p,
            top_k=query.top_k,
            num_predict=query.num_predict,
            stream=False
        )

        response = QueryResponse(
            response=result.get("response", ""),
            model=query.model,
            prompt=query.prompt,
            total_duration=result.get("total_duration"),
            load_duration=result.get("load_duration")
        )

        duration = (time.time() - start_time) * 1000
        log_response(logger, "POST", "/api/ask", 200, duration)

        return response

    except (OllamaConnectionError, OllamaError) as e:
        logger.error(f"LLM error: {e.detail}")
        duration = (time.time() - start_time) * 1000
        log_response(logger, "POST", "/api/ask", e.status_code, duration)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in ask endpoint: {e}")
        duration = (time.time() - start_time) * 1000
        log_response(logger, "POST", "/api/ask", 500, duration)
        raise OllamaError(f"Error processing request: {str(e)}")


@router.post("/ask/stream")
async def ask_llm_stream(
    query: QueryRequest,
    request: Request,
    client_ip: str = Depends(apply_rate_limit)
):
    """
    Stream response from the LLM

    Returns streamed tokens as they are generated.
    """
    start_time = time.time()
    log_request(logger, "POST", "/api/ask/stream", client_ip)

    try:
        ollama_service = get_ollama_service()

        async def generate():
            try:
                response_iter = ollama_service.generate(
                    prompt=query.prompt,
                    model=query.model,
                    temperature=query.temperature,
                    top_p=query.top_p,
                    top_k=query.top_k,
                    num_predict=query.num_predict,
                    stream=True
                )

                for chunk in response_iter:
                    if isinstance(chunk, dict) and "response" in chunk:
                        yield json.dumps({
                            "token": chunk["response"],
                            "model": query.model
                        }).encode() + b"\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield json.dumps({"error": str(e)}).encode()

        duration = (time.time() - start_time) * 1000
        log_response(logger, "POST", "/api/ask/stream", 200, duration)

        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson"
        )

    except (OllamaConnectionError, OllamaError) as e:
        logger.error(f"LLM streaming error: {e.detail}")
        duration = (time.time() - start_time) * 1000
        log_response(logger, "POST", "/api/ask/stream", e.status_code, duration)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in ask/stream endpoint: {e}")
        duration = (time.time() - start_time) * 1000
        log_response(logger, "POST", "/api/ask/stream", 500, duration)
        raise OllamaError(f"Streaming error: {str(e)}")


@router.get("/")
async def root(request: Request):
    """Root endpoint"""
    client_ip = get_client_ip(request)
    log_request(logger, "GET", "/", client_ip)

    return {
        "message": "Local LLM Server Running 🚀",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "ask": "/api/ask",
            "ask_stream": "/api/ask/stream",
            "models": "/api/models",
            "docs": "/docs"
        }
    }
