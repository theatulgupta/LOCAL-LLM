"""Rate limiting middleware"""

import time
from collections import defaultdict
from typing import Dict, Tuple
import logging

from app.config import get_settings
from app.utils.exceptions import RateLimitExceededError

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter implementation"""

    def __init__(self):
        self.settings = get_settings()
        self.requests: Dict[str, list] = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        """
        Check if request from client is allowed

        Args:
            client_id: Unique client identifier (IP address)

        Returns:
            True if request is allowed, False otherwise

        Raises:
            RateLimitExceededError: If rate limit is exceeded
        """
        if not self.settings.rate_limit_enabled:
            return True

        current_time = time.time()
        window_start = current_time - self.settings.rate_limit_window_seconds

        # Clean old requests outside the window
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]

        # Check if within limit
        if len(self.requests[client_id]) >= self.settings.rate_limit_requests:
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            raise RateLimitExceededError(
                f"Rate limit exceeded: {self.settings.rate_limit_requests} "
                f"requests per {self.settings.rate_limit_window_seconds} seconds"
            )

        # Add current request
        self.requests[client_id].append(current_time)
        return True

    def get_remaining_requests(self, client_id: str) -> int:
        """Get remaining request quota for client"""
        if not self.settings.rate_limit_enabled:
            return -1

        current_time = time.time()
        window_start = current_time - self.settings.rate_limit_window_seconds

        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]

        return max(0, self.settings.rate_limit_requests - len(self.requests[client_id]))


# Singleton instance
_rate_limiter: RateLimiter = None


def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
