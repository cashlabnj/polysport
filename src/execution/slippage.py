from __future__ import annotations


def within_slippage(expected_price: float, actual_price: float, max_slippage: float) -> bool:
    if expected_price <= 0:
        return False
    slippage = abs(actual_price - expected_price) / expected_price
    return slippage <= max_slippage
