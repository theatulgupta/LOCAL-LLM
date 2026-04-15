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
from app.services.rag_service import get_rag_service
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
    Send a query to the LLM with optional RAG context from lab notes

    Returns the generated response from the model, enriched with local context.
    """
    start_time = time.time()
    log_request(logger, "POST", "/api/ask", client_ip)

    try:
        ollama_service = get_ollama_service()
        rag_service = get_rag_service()

        logger.debug(f"Processing query from {client_ip}: {query.prompt[:50]}...")

        # Enrich prompt with RAG context if enabled
        final_prompt = query.prompt
        rag_context = None
        if rag_service.is_enabled():
            final_prompt, rag_context = rag_service.build_prompt(query.prompt)
            logger.debug(f"RAG enriched prompt with {len(rag_context.sources)} sources")

        result = ollama_service.generate(
            prompt=final_prompt,
            model=query.model,
            temperature=query.temperature,
            top_p=query.top_p,
            top_k=query.top_k,
            num_predict=query.num_predict,
            stream=False
        )

        response_dict = {
            "response": result.get("response", ""),
            "model": query.model,
            "prompt": query.prompt,
            "total_duration": result.get("total_duration"),
            "load_duration": result.get("load_duration")
        }

        # Add RAG metadata if context was used
        if rag_context:
            response_dict["rag"] = {
                "enabled": True,
                "sources_count": len(rag_context.sources),
                "corpus_path": rag_context.corpus_path,
                "indexed_files": rag_context.indexed_files,
                "indexed_chunks": rag_context.indexed_chunks
            }
        else:
            response_dict["rag"] = {"enabled": False}

        response = QueryResponse(**response_dict)

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
    Stream response from the LLM with RAG context

    Returns streamed tokens as they are generated, enriched with local context.
    """
    start_time = time.time()
    log_request(logger, "POST", "/api/ask/stream", client_ip)

    try:
        ollama_service = get_ollama_service()
        rag_service = get_rag_service()

        async def generate():
            try:
                # Enrich prompt with RAG context if enabled
                final_prompt = query.prompt
                rag_context = None
                if rag_service.is_enabled():
                    final_prompt, rag_context = rag_service.build_prompt(query.prompt)
                    logger.debug(f"RAG enriched stream prompt with {len(rag_context.sources)} sources")

                # Send RAG metadata first if available
                if rag_context:
                    yield json.dumps({
                        "type": "rag_metadata",
                        "enabled": True,
                        "sources_count": len(rag_context.sources),
                        "corpus_path": rag_context.corpus_path
                    }).encode() + b"\n"

                response_iter = ollama_service.generate(
                    prompt=final_prompt,
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
                            "type": "token",
                            "token": chunk["response"],
                            "model": query.model
                        }).encode() + b"\n"
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                yield json.dumps({"type": "error", "error": str(e)}).encode() + b"\n"

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


@router.get("/rag/status")
async def rag_status(request: Request, client_ip: str = Depends(apply_rate_limit)):
    """Get RAG service status and indexing info"""
    start_time = time.time()
    log_request(logger, "GET", "/api/rag/status", client_ip)

    try:
        rag_service = get_rag_service()
        status = rag_service.status()

        duration = (time.time() - start_time) * 1000
        log_response(logger, "GET", "/api/rag/status", 200, duration)

        return status
    except Exception as e:
        logger.error(f"Error getting RAG status: {e}")
        duration = (time.time() - start_time) * 1000
        log_response(logger, "GET", "/api/rag/status", 500, duration)
        raise OllamaError(f"Error retrieving RAG status: {str(e)}")


@router.post("/rag/search")
async def rag_search(
    request: Request,
    query: str = Query(..., min_length=1, description="Search query"),
    top_k: int = Query(3, ge=1, le=10, description="Number of top results"),
    client_ip: str = Depends(apply_rate_limit)
):
    """Search the local notebook corpus"""
    start_time = time.time()
    log_request(logger, "GET", "/api/rag/search", client_ip)

    try:
        rag_service = get_rag_service()
        context = rag_service.search(query, top_k=top_k)

        result = {
            "question": context.question,
            "context": context.context,
            "sources": [
                {
                    "path": src.source_path,
                    "chunk_index": src.chunk_index,
                    "score": src.score,
                    "snippet": src.snippet,
                    "cell_type": src.cell_type,
                    "cell_id": src.cell_id
                }
                for src in context.sources
            ],
            "enabled": context.enabled,
            "indexed_files": context.indexed_files,
            "indexed_chunks": context.indexed_chunks
        }

        duration = (time.time() - start_time) * 1000
        log_response(logger, "GET", "/api/rag/search", 200, duration)

        return result
    except Exception as e:
        logger.error(f"Error searching RAG corpus: {e}")
        duration = (time.time() - start_time) * 1000
        log_response(logger, "GET", "/api/rag/search", 500, duration)
        raise OllamaError(f"Error searching corpus: {str(e)}")


@router.post("/rag/refresh")
async def rag_refresh(request: Request, client_ip: str = Depends(apply_rate_limit)):
    """Force refresh the RAG index"""
    start_time = time.time()
    log_request(logger, "POST", "/api/rag/refresh", client_ip)

    try:
        rag_service = get_rag_service()
        rag_service.refresh()
        status = rag_service.status()

        duration = (time.time() - start_time) * 1000
        log_response(logger, "POST", "/api/rag/refresh", 200, duration)

        return {"message": "RAG index refreshed", **status}
    except Exception as e:
        logger.error(f"Error refreshing RAG index: {e}")
        duration = (time.time() - start_time) * 1000
        log_response(logger, "POST", "/api/rag/refresh", 500, duration)
        raise OllamaError(f"Error refreshing RAG index: {str(e)}")


@router.get("/")
async def root(request: Request):
    """Root endpoint"""
    client_ip = get_client_ip(request)
    log_request(logger, "GET", "/", client_ip)

    return {
        "message": "Local LLM Server with RAG 🚀",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "ask": "/api/ask",
            "ask_stream": "/api/ask/stream",
            "models": "/api/models",
            "rag_status": "/api/rag/status",
            "rag_search": "/api/rag/search",
            "rag_refresh": "/api/rag/refresh",
            "docs": "/docs"
        }
    }
