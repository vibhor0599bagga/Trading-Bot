"""
Binance Futures Testnet REST client.
Handles authentication (HMAC-SHA256 signing), request execution,
logging, and error handling. No business logic lives here.
"""

import hashlib
import hmac
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from bot.logging_config import get_logger

logger = get_logger(__name__)

TESTNET_BASE_URL = "https://testnet.binancefuture.com"
DEFAULT_TIMEOUT = 10  # seconds
RECV_WINDOW = 5000    # milliseconds


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
        base_url: str = TESTNET_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        if not api_key or not api_secret:
            raise ValueError("Both api_key and api_secret must be provided.")
        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "X-MBX-APIKEY": self._api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.debug("BinanceClient initialised (base_url=%s)", self._base_url)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _timestamp(self) -> int:
        return int(time.time() * 1000)

    def _sign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add timestamp + HMAC-SHA256 signature to params dict."""
        params["timestamp"] = self._timestamp()
        params["recvWindow"] = RECV_WINDOW
        query_string = urlencode(params)
        signature = hmac.new(
            self._api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a signed HTTP request.
        Logs request params (DEBUG) and response body (DEBUG).
        Raises BinanceAPIError on API-level errors.
        Raises requests.exceptions.* on network/timeout failures.
        """
        params = params or {}
        signed_params = self._sign(params.copy())

        url = f"{self._base_url}{endpoint}"
        logger.debug("REQUEST  %s %s | params=%s", method.upper(), endpoint, signed_params)

        try:
            if method.upper() == "POST":
                resp = self._session.post(url, data=signed_params, timeout=self._timeout)
            elif method.upper() == "GET":
                resp = self._session.get(url, params=signed_params, timeout=self._timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            logger.debug(
                "RESPONSE %s %s | status=%d | body=%s",
                method.upper(),
                endpoint,
                resp.status_code,
                resp.text,
            )

            data = resp.json()

            # Binance error payload: {"code": -XXXX, "msg": "..."}
            if isinstance(data, dict) and data.get("code", 0) < 0:
                raise BinanceAPIError(
                    status_code=resp.status_code,
                    code=data["code"],
                    message=data.get("msg", "Unknown error"),
                )

            resp.raise_for_status()
            return data

        except requests.exceptions.Timeout:
            logger.error("Request timed out: %s %s", method.upper(), endpoint)
            raise
        except requests.exceptions.ConnectionError as exc:
            logger.error("Connection error: %s %s | %s", method.upper(), endpoint, exc)
            raise
        except BinanceAPIError:
            raise
        except requests.exceptions.HTTPError as exc:
            logger.error("HTTP error: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def place_order(self, **kwargs) -> Dict[str, Any]:
        """
        POST /fapi/v1/order
        Accepts keyword arguments matching Binance order params.
        Returns the raw order response dict.
        """
        logger.info(
            "Placing order → symbol=%s side=%s type=%s qty=%s price=%s",
            kwargs.get("symbol"),
            kwargs.get("side"),
            kwargs.get("type"),
            kwargs.get("quantity"),
            kwargs.get("price", "N/A"),
        )
        return self._request("POST", "/fapi/v1/order", params=kwargs)

    def get_exchange_info(self) -> Dict[str, Any]:
        """GET /fapi/v1/exchangeInfo — useful for validating symbols."""
        return self._request("GET", "/fapi/v1/exchangeInfo", params={})

    def get_account(self) -> Dict[str, Any]:
        """GET /fapi/v2/account — returns account balance and positions."""
        return self._request("GET", "/fapi/v2/account", params={})
