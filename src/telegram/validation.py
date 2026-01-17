from __future__ import annotations

import re


# Validation patterns
SAFE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
SAFE_MARKET_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")
SAFE_PARAM_PATTERN = re.compile(r"^[a-zA-Z0-9_.]{1,64}$")


def validate_strategy_name(name: str) -> bool:
    """Validate a strategy name is safe."""
    return bool(SAFE_NAME_PATTERN.match(name))


def validate_market_id(market_id: str) -> bool:
    """Validate a market ID is safe."""
    return bool(SAFE_MARKET_ID_PATTERN.match(market_id))


def validate_param_name(param: str) -> bool:
    """Validate a parameter name is safe."""
    return bool(SAFE_PARAM_PATTERN.match(param))


def validate_numeric_value(value: str, min_val: float = 0.0, max_val: float = 1e9) -> float | None:
    """Validate and parse a numeric value within bounds."""
    try:
        parsed = float(value)
        if min_val <= parsed <= max_val:
            return parsed
        return None
    except ValueError:
        return None


def sanitize_log_message(message: str, max_length: int = 500) -> str:
    """Sanitize a message for logging (remove sensitive chars, truncate)."""
    # Remove control characters
    sanitized = "".join(c if c.isprintable() or c.isspace() else "?" for c in message)
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    return sanitized
