"""Custom exception classes for the application"""

from fastapi import HTTPException, status


class OllamaConnectionError(HTTPException):
    """Raised when unable to connect to Ollama server"""

    def __init__(self, detail: str = "Unable to connect to Ollama server"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )


class InvalidPromptError(HTTPException):
    """Raised when prompt validation fails"""

    def __init__(self, detail: str = "Invalid prompt provided"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class OllamaError(HTTPException):
    """Raised when Ollama returns an error"""

    def __init__(self, detail: str = "Error from Ollama server"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class RateLimitExceededError(HTTPException):
    """Raised when rate limit is exceeded"""

    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )
