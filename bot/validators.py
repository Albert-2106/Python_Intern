"""
Input validation for order parameters.
All validation errors raise ValueError with a descriptive message.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


def validate_symbol(symbol: str) -> str:
    """Ensure symbol is a non-empty uppercase string."""
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("Symbol cannot be empty.")
    if not symbol.isalnum():
        raise ValueError(f"Invalid symbol '{symbol}': must be alphanumeric (e.g. BTCUSDT).")
    return symbol


def validate_side(side: str) -> str:
    """Ensure side is BUY or SELL (case-insensitive)."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(f"Invalid side '{side}': must be one of {sorted(VALID_SIDES)}.")
    return side


def validate_order_type(order_type: str) -> str:
    """Ensure order_type is one of the supported types."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}': must be one of {sorted(VALID_ORDER_TYPES)}."
        )
    return order_type


def validate_quantity(quantity: str | float) -> Decimal:
    """Ensure quantity is a positive number."""
    try:
        qty = Decimal(str(quantity))
    except InvalidOperation:
        raise ValueError(f"Invalid quantity '{quantity}': must be a numeric value.")
    if qty <= 0:
        raise ValueError(f"Quantity must be greater than zero, got {qty}.")
    return qty


def validate_price(price: Optional[str | float], order_type: str) -> Optional[Decimal]:
    """
    Validate price based on order type.
    - LIMIT / STOP_MARKET: price must be provided and positive.
    - MARKET: price is ignored (returns None).
    """
    if order_type == "MARKET":
        if price is not None:
            # Silently ignore — user may have passed it by accident
            pass
        return None

    if price is None:
        raise ValueError(f"Price is required for {order_type} orders.")

    try:
        p = Decimal(str(price))
    except InvalidOperation:
        raise ValueError(f"Invalid price '{price}': must be a numeric value.")

    if p <= 0:
        raise ValueError(f"Price must be greater than zero, got {p}.")

    return p


def validate_stop_price(stop_price: Optional[str | float], order_type: str) -> Optional[Decimal]:
    """Validate stop price for STOP_MARKET orders."""
    if order_type != "STOP_MARKET":
        return None

    if stop_price is None:
        raise ValueError("stop_price is required for STOP_MARKET orders.")

    try:
        sp = Decimal(str(stop_price))
    except InvalidOperation:
        raise ValueError(f"Invalid stop_price '{stop_price}': must be a numeric value.")

    if sp <= 0:
        raise ValueError(f"stop_price must be greater than zero, got {sp}.")

    return sp


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: Optional[str | float] = None,
    stop_price: Optional[str | float] = None,
) -> dict:
    """
    Run all validations and return a clean params dict ready for the API layer.
    Raises ValueError on the first invalid field encountered.
    """
    clean_symbol = validate_symbol(symbol)
    clean_side = validate_side(side)
    clean_type = validate_order_type(order_type)
    clean_qty = validate_quantity(quantity)
    clean_price = validate_price(price, clean_type)
    clean_stop = validate_stop_price(stop_price, clean_type)

    params: dict = {
        "symbol": clean_symbol,
        "side": clean_side,
        "order_type": clean_type,
        "quantity": clean_qty,
    }
    if clean_price is not None:
        params["price"] = clean_price
    if clean_stop is not None:
        params["stop_price"] = clean_stop

    return params
