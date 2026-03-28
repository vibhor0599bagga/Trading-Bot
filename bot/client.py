"""
Binance Futures Testnet client with manual HMAC signing.
Handles authentication, request execution, logging, and error handling.
"""

import os
import time
import hmac
import hashlib
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from bot.logging_config import get_logger

logger = get_logger(__name__)

# Default to documented futures testnet host; override via BASE_URL env or constructor.
TESTNET_BASE_URL = "https://demo-fapi.binance.com"
DEFAULT_TIMEOUT = 10  # seconds


class BinanceAPIError(Exception):
    """Raised when Binance returns a non-2xx status or an error payload."""

    def __init__(self, status_code: int, code: int, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(f"Binance API error {code}: {message} (HTTP {status_code})")


class BinanceClient:
    """
    Thin wrapper around the Binance Futures REST API (USDT-M).

    Usage:
        client = BinanceClient(api_key="...", api_secret="...")
        response = client.place_order(symbol="BTCUSDT", side="BUY", ...)
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        api_key = api_key.strip()
        api_secret = api_secret.strip()
        if not api_key or not api_secret:
            raise ValueError("Both api_key and api_secret must be provided.")
        self._api_key = api_key
        self._api_secret = api_secret
        env_base_url = os.getenv("BASE_URL", "").strip()
        resolved_base_url = base_url or env_base_url or TESTNET_BASE_URL
        self._base_url = resolved_base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"X-MBX-APIKEY": self._api_key})
        logger.debug("BinanceClient initialised (base_url=%s)", self._base_url)

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def place_order(self, **kwargs) -> Dict[str, Any]:
        """
        POST /fapi/v1/order — places an order with manual HMAC signing.
        Quantity is stringified to avoid float drift.
        """
        if "quantity" in kwargs and kwargs["quantity"] is not None:
            kwargs = {**kwargs, "quantity": str(kwargs["quantity"])}

        logger.info(
            "Placing order → symbol=%s side=%s type=%s qty=%s price=%s",
            kwargs.get("symbol"),
            kwargs.get("side"),
            kwargs.get("type"),
            kwargs.get("quantity"),
            kwargs.get("price", "N/A"),
        )
        return self._signed_request("POST", "/fapi/v1/order", kwargs)

    def get_exchange_info(self) -> Dict[str, Any]:
        """GET /fapi/v1/exchangeInfo — useful for validating symbols."""
        return self._request("GET", "/fapi/v1/exchangeInfo", params=None, signed=False)

    def get_account(self) -> Dict[str, Any]:
        """GET /fapi/v2/account — returns account balance and positions."""
        return self._signed_request("GET", "/fapi/v2/account", params=None)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Any],
        signed: bool,
    ) -> Dict[str, Any]:
        url = f"{self._base_url}{path}"
        response = self._session.request(
            method=method,
            url=url,
            params=params,
            timeout=self._timeout,
        )
        return self._handle_response(response)

    def _signed_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        params = params.copy() if params else {}
        params.setdefault("timestamp", int(time.time() * 1000))
        params.setdefault("recvWindow", 5000)

        # Sort parameters before signing to ensure deterministic query string.
        sorted_items = sorted(params.items())
        query_string = urlencode(sorted_items, doseq=True)
        logger.info("query_string=%s", query_string)

        signature = hmac.new(
            self._api_secret.encode(),
            query_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        signed_items = list(sorted_items) + [("signature", signature)]

        return self._request(method, path, signed_items, signed=True)

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        if response.status_code // 100 != 2:
            try:
                payload = response.json()
                code = payload.get("code", -1)
                message = payload.get("msg", response.text)
            except Exception:
                payload = None
                code = -1
                message = response.text
            logger.error(
                "Binance HTTP error: status=%s code=%s msg=%s body=%s",
                response.status_code,
                code,
                message,
                payload,
            )
            raise BinanceAPIError(response.status_code, code, message)

        try:
            return response.json()
        except ValueError:
            logger.error("Failed to decode JSON response: %s", response.text)
            raise BinanceAPIError(response.status_code, -1, "Invalid JSON response")
