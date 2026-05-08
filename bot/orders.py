"""
Order placement logic — sits between the CLI layer and the API client.

Responsible for:
- Calling validators before any API call
- Delegating to BinanceClient
- Formatting and returning structured order results
- Logging order summaries
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional

from .client import BinanceClient
from .logging_config import get_logger
from .validators import validate_all

logger = get_logger("orders")


def _format_result(raw: dict) -> Dict[str, Any]:
    """Extract the most useful fields from a raw Binance order response."""
    return {
        "orderId": raw.get("orderId"),
        "symbol": raw.get("symbol"),
        "side": raw.get("side"),
        "type": raw.get("type"),
        "origQty": raw.get("origQty"),
        "executedQty": raw.get("executedQty"),
        "avgPrice": raw.get("avgPrice"),
        "price": raw.get("price"),
        "stopPrice": raw.get("stopPrice"),
        "status": raw.get("status"),
        "timeInForce": raw.get("timeInForce"),
        "updateTime": raw.get("updateTime"),
    }


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | float,
    price: Optional[str | float] = None,
    stop_price: Optional[str | float] = None,
    time_in_force: str = "GTC",
) -> Dict[str, Any]:
    """
    Validate inputs and place a futures order via the provided client.

    Args:
        client:       Authenticated BinanceClient instance.
        symbol:       Trading pair (e.g. 'BTCUSDT').
        side:         'BUY' or 'SELL'.
        order_type:   'MARKET', 'LIMIT', or 'STOP_MARKET'.
        quantity:     Order quantity.
        price:        Limit price (LIMIT orders only).
        stop_price:   Stop trigger price (STOP_MARKET orders only).
        time_in_force: 'GTC' | 'IOC' | 'FOK' (LIMIT only).

    Returns:
        Formatted dict with key order details.

    Raises:
        ValueError:       On validation failure.
        BinanceAPIError:  On API-level rejection.
        requests.*:       On network failures.
    """
    # ---- Validate ----
    params = validate_all(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
    )

    logger.info(
        "Order request | symbol=%s side=%s type=%s qty=%s price=%s stopPrice=%s",
        params["symbol"],
        params["side"],
        params["order_type"],
        params["quantity"],
        params.get("price"),
        params.get("stop_price"),
    )

    # ---- Place ----
    raw_response = client.place_order(
        symbol=params["symbol"],
        side=params["side"],
        order_type=params["order_type"],
        quantity=params["quantity"],
        price=params.get("price"),
        stop_price=params.get("stop_price"),
        time_in_force=time_in_force,
    )

    result = _format_result(raw_response)

    logger.info(
        "Order placed ✓ | orderId=%s status=%s executedQty=%s avgPrice=%s",
        result["orderId"],
        result["status"],
        result["executedQty"],
        result["avgPrice"],
    )

    return result
