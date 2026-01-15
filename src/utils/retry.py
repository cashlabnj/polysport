from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


def retry(operation: Callable[[], T], attempts: int = 3, delay_s: float = 0.5) -> T:
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            return operation()
        except Exception as exc:  # noqa: BLE001 - intent is to retry any error
            last_error = exc
            time.sleep(delay_s)
    raise RuntimeError("operation failed after retries") from last_error
