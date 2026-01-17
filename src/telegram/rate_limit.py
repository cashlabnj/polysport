from __future__ import annotations

from collections import defaultdict
from time import time


class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests: dict[int, list[float]] = defaultdict(list)

    def is_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to make a request."""
        now = time()
        # Clean old requests outside the window
        self.requests[user_id] = [
            t for t in self.requests[user_id] if now - t < self.window
        ]
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        self.requests[user_id].append(now)
        return True

    def reset(self, user_id: int) -> None:
        """Reset rate limit for a specific user."""
        self.requests[user_id] = []

    def remaining(self, user_id: int) -> int:
        """Get remaining requests for a user."""
        now = time()
        self.requests[user_id] = [
            t for t in self.requests[user_id] if now - t < self.window
        ]
        return max(0, self.max_requests - len(self.requests[user_id]))
