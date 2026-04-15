"""Logging utilities for the application"""

import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance"""
    return logging.getLogger(name)


def log_request(logger: logging.Logger, method: str, path: str, ip: str) -> None:
    """Log incoming API request"""
    logger.info(f"Request: {method} {path} from {ip}")


def log_response(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float
) -> None:
    """Log API response"""
    logger.info(
        f"Response: {method} {path} - {status_code} ({duration_ms:.2f}ms)"
    )


def log_ollama_call(
    logger: logging.Logger,
    model: str,
    prompt_length: int
) -> None:
    """Log Ollama API call"""
    logger.debug(f"Calling Ollama with model={model}, prompt_length={prompt_length}")
