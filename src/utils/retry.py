from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


class RetryError(Exception):
    """Raised when all retry attempts fail."""

    def __init__(self, message: str, attempts: int, last_error: Exception | None = None) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.last_error = last_error


def retry(
    operation: Callable[[], T],
    attempts: int = 3,
    base_delay_s: float = 0.5,
    max_delay_s: float = 30.0,
    exponential: bool = True,
    jitter: bool = True,
    retryable_exceptions: tuple[type[Exception], ...] | None = None,
) -> T:
    """Retry an operation with configurable backoff.

    Args:
        operation: The operation to retry
        attempts: Maximum number of attempts
        base_delay_s: Initial delay between retries
        max_delay_s: Maximum delay between retries
        exponential: Use exponential backoff if True, fixed delay if False
        jitter: Add random jitter to delays to prevent thundering herd
        retryable_exceptions: Tuple of exception types to retry on. If None, retry on all exceptions.

    Returns:
        The result of the operation

    Raises:
        RetryError: If all attempts fail
    """
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            return operation()
        except Exception as exc:
            # Check if this exception should be retried
            if retryable_exceptions is not None and not isinstance(exc, retryable_exceptions):
                raise

            last_error = exc
            is_last_attempt = attempt >= attempts - 1

            if is_last_attempt:
                break

            # Calculate delay with exponential backoff
            if exponential:
                delay = min(base_delay_s * (2**attempt), max_delay_s)
            else:
                delay = base_delay_s

            # Add jitter (0.5x to 1.5x)
            if jitter:
                delay *= 0.5 + random.random()

            logger.warning(
                "retry_attempt",
                extra={
                    "attempt": attempt + 1,
                    "max_attempts": attempts,
                    "delay_s": delay,
                    "error": str(exc),
                },
            )

            time.sleep(delay)

    raise RetryError(
        f"Operation failed after {attempts} attempts",
        attempts=attempts,
        last_error=last_error,
    )


def retry_with_timeout(
    operation: Callable[[], T],
    timeout_s: float,
    base_delay_s: float = 0.5,
    max_delay_s: float = 5.0,
) -> T:
    """Retry an operation until timeout.

    Args:
        operation: The operation to retry
        timeout_s: Total timeout in seconds
        base_delay_s: Initial delay between retries
        max_delay_s: Maximum delay between retries

    Returns:
        The result of the operation

    Raises:
        RetryError: If timeout is reached
    """
    start_time = time.monotonic()
    last_error: Exception | None = None
    attempt = 0

    while time.monotonic() - start_time < timeout_s:
        try:
            return operation()
        except Exception as exc:
            last_error = exc
            attempt += 1

            # Calculate remaining time
            elapsed = time.monotonic() - start_time
            remaining = timeout_s - elapsed

            if remaining <= 0:
                break

            # Calculate delay with exponential backoff
            delay = min(base_delay_s * (2 ** (attempt - 1)), max_delay_s, remaining)

            # Add jitter
            delay *= 0.5 + random.random()

            logger.warning(
                "retry_attempt_timeout",
                extra={
                    "attempt": attempt,
                    "elapsed_s": elapsed,
                    "remaining_s": remaining,
                    "delay_s": delay,
                    "error": str(exc),
                },
            )

            time.sleep(min(delay, remaining))

    raise RetryError(
        f"Operation timed out after {timeout_s}s ({attempt} attempts)",
        attempts=attempt,
        last_error=last_error,
    )
