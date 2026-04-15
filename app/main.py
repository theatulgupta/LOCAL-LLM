"""Main FastAPI application"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import time

from app.config import setup_logging, get_settings
from app.routes import llm
from app.utils.exceptions import (
    OllamaConnectionError,
    InvalidPromptError,
    OllamaError,
    RateLimitExceededError
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    settings = get_settings()

    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description="Production-grade local LLM server with Ollama and FastAPI",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure based on your needs
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure based on your needs
    )

    # Add request/response logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Middleware to log requests and responses"""
        start_time = time.time()

        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(f"Request failed: {exc}")
            raise

        process_time = (time.time() - start_time) * 1000
        response.headers["X-Process-Time"] = str(process_time)

        return response

    # Exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors"""
        logger.warning(f"Validation error: {exc}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "detail": exc.errors(),
                "status_code": 422
            }
        )

    @app.exception_handler(OllamaConnectionError)
    async def ollama_connection_error_handler(request: Request, exc: OllamaConnectionError):
        """Handle Ollama connection errors"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "Ollama Connection Error",
                "detail": exc.detail,
                "status_code": exc.status_code
            }
        )

    @app.exception_handler(OllamaError)
    async def ollama_error_handler(request: Request, exc: OllamaError):
        """Handle Ollama errors"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "Ollama Error",
                "detail": exc.detail,
                "status_code": exc.status_code
            }
        )

    @app.exception_handler(RateLimitExceededError)
    async def rate_limit_error_handler(request: Request, exc: RateLimitExceededError):
        """Handle rate limit errors"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "Rate Limit Exceeded",
                "detail": exc.detail,
                "status_code": exc.status_code
            }
        )

    @app.exception_handler(InvalidPromptError)
    async def invalid_prompt_error_handler(request: Request, exc: InvalidPromptError):
        """Handle invalid prompt errors"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "Invalid Prompt",
                "detail": exc.detail,
                "status_code": exc.status_code
            }
        )

    # Include routers
    app.include_router(llm.router)

    # Startup events
    @app.on_event("startup")
    async def startup_event():
        """Startup event handler"""
        logger.info(f"Starting {settings.api_title} v{settings.api_version}")
        logger.info(f"Ollama server at: {settings.ollama_host}")
        logger.info(f"Rate limiting: {'Enabled' if settings.rate_limit_enabled else 'Disabled'}")

    # Shutdown events
    @app.on_event("shutdown")
    async def shutdown_event():
        """Shutdown event handler"""
        logger.info("Shutting down application")

    return app


# Create the application
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
