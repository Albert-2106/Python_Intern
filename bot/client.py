"""
Binance Futures Testnet REST API client.

Handles authentication (HMAC-SHA256), request signing, HTTP execution,
and raw response parsing. This layer knows nothing about CLI or business logic.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from decimal import Decimal
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from .logging_config import get_logger

logger = get_logger("client")

# Binance Futures Testnet base URL
BASE_URL = "https://testnet.binancefuture.com"
RECV_WINDOW = 5000  # milliseconds


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, msg: str, http_status: int = 0):
        self.code = code
        self.msg = msg
        self.http_status = http_status
        super().__init__(f"Binance API Error {code}: {msg} (HTTP {http_status})")


class BinanceClient:
    """
    Thin wrapper around the Binance Futures REST API.

    All public methods return parsed JSON dicts.
    Network and API errors are re-raised as BinanceAPIError or requests exceptions.
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = BASE_URL):
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret must not be empty.")

        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")

        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.info("BinanceClient initialised — base URL: %s", self.base_url)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, params: dict) -> str:
        query = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        signed: bool = False,
    ) -> Any:
        url = f"{self.base_url}{endpoint}"
        params = params or {}

        if signed:
            params["timestamp"] = self._timestamp()
            params["recvWindow"] = RECV_WINDOW
            params["signature"] = self._sign(params)

        logger.debug("→ %s %s  params=%s", method.upper(), endpoint, params)

        try:
            if method.upper() == "GET":
                response = self._session.get(url, params=params, timeout=10)
            elif method.upper() == "POST":
                response = self._session.post(url, data=params, timeout=10)
            elif method.upper() == "DELETE":
                response = self._session.delete(url, params=params, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        except requests.exceptions.ConnectionError as exc:
            logger.error("Network connection error: %s", exc)
            raise
        except requests.exceptions.Timeout as exc:
            logger.error("Request timed out: %s", exc)
            raise

        logger.debug("← HTTP %s  body=%s", response.status_code, response.text[:500])

        try:
            data = response.json()
        except ValueError:
            logger.error("Non-JSON response (HTTP %s): %s", response.status_code, response.text)
            response.raise_for_status()
            return {}

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            code = data.get("code", -1)
            msg = data.get("msg", "Unknown error")
            logger.error("API error %s: %s", code, msg)
            raise BinanceAPIError(code, msg, response.status_code)

        if not response.ok:
            logger.error("HTTP error %s: %s", response.status_code, data)
            response.raise_for_status()

        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_exchange_info(self) -> dict:
        """Fetch exchange trading rules and symbol metadata."""
        return self._request("GET", "/fapi/v1/exchangeInfo")

    def get_account(self) -> dict:
        """Fetch account info (balances, positions)."""
        return self._request("GET", "/fapi/v2/account", signed=True)

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        time_in_force: str = "GTC",
    ) -> dict:
        """
        Place a new futures order.

        Args:
            symbol:        Trading pair, e.g. 'BTCUSDT'
            side:          'BUY' or 'SELL'
            order_type:    'MARKET', 'LIMIT', or 'STOP_MARKET'
            quantity:      Order quantity
            price:         Limit price (required for LIMIT)
            stop_price:    Stop trigger price (required for STOP_MARKET)
            time_in_force: GTC / IOC / FOK (ignored for MARKET)

        Returns:
            Raw order response dict from Binance.
        """
        params: Dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
        }

        if order_type == "LIMIT":
            if price is None:
                raise ValueError("price is required for LIMIT orders.")
            params["price"] = str(price)
            params["timeInForce"] = time_in_force

        if order_type == "STOP_MARKET":
            if stop_price is None:
                raise ValueError("stop_price is required for STOP_MARKET orders.")
            params["stopPrice"] = str(stop_price)

        logger.info(
            "Placing %s %s order | symbol=%s qty=%s price=%s stopPrice=%s",
            side,
            order_type,
            symbol,
            quantity,
            price,
            stop_price,
        )
        return self._request("POST", "/fapi/v1/order", params=params, signed=True)

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """Cancel an open order by orderId."""
        params = {"symbol": symbol, "orderId": order_id}
        logger.info("Cancelling orderId=%s for %s", order_id, symbol)
        return self._request("DELETE", "/fapi/v1/order", params=params, signed=True)

    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        """List all open orders, optionally filtered by symbol."""
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request("GET", "/fapi/v1/openOrders", params=params, signed=True)

    def close(self) -> None:
        self._session.close()
        logger.debug("HTTP session closed.")
