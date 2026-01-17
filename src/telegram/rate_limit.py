from __future__ import annotations

from collections import defaultdict
from time import time


# Maximum number of users to track before cleanup
MAX_TRACKED_USERS = 10000
# Cleanup interval (every N requests, perform cleanup)
CLEANUP_INTERVAL = 100


class RateLimiter:
    """Simple in-memory rate limiter using sliding window with automatic cleanup."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests: dict[int, list[float]] = defaultdict(list)
        self._request_count = 0

    def _cleanup_stale_users(self) -> None:
        """Remove users with no recent activity to prevent memory growth."""
        now = time()
        stale_users = [
            user_id
            for user_id, timestamps in self.requests.items()
            if not timestamps or (now - max(timestamps)) > self.window * 2
        ]
        for user_id in stale_users:
            del self.requests[user_id]

    def is_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to make a request."""
        now = time()

        # Periodic cleanup to prevent memory leaks
        self._request_count += 1
        if self._request_count >= CLEANUP_INTERVAL:
            self._cleanup_stale_users()
            self._request_count = 0

        # Clean old requests for this user
        self.requests[user_id] = [
            t for t in self.requests[user_id] if now - t < self.window
        ]

        if len(self.requests[user_id]) >= self.max_requests:
            return False

        self.requests[user_id].append(now)
        return True

    def reset(self, user_id: int) -> None:
        """Reset rate limit for a specific user."""
        if user_id in self.requests:
            del self.requests[user_id]

    def remaining(self, user_id: int) -> int:
        """Get remaining requests for a user."""
        now = time()
        self.requests[user_id] = [
            t for t in self.requests[user_id] if now - t < self.window
        ]
        return max(0, self.max_requests - len(self.requests[user_id]))

    def active_users(self) -> int:
        """Get count of currently tracked users (for monitoring)."""
        return len(self.requests)
