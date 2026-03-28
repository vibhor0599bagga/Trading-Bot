"""
Order placement logic.
Bridges the CLI layer and the Binance client.
Handles payload construction, response parsing, and structured logging.
"""

from typing import Any, Dict, Optional

from bot.client import BinanceClient
from bot.logging_config import get_logger
from bot.validators import validate_all

logger = get_logger(__name__)


class OrderResult:
    """Parsed, human-friendly representation of a Binance order response."""

    def __init__(self, raw: Dict[str, Any]):
        self.raw = raw
        self.order_id: int = raw.get("orderId", 0)
        self.client_order_id: str = raw.get("clientOrderId", "")
        self.symbol: str = raw.get("symbol", "")
        self.side: str = raw.get("side", "")
        self.order_type: str = raw.get("type", "")
        self.status: str = raw.get("status", "")
        self.price: str = raw.get("price", "0")
        self.avg_price: str = raw.get("avgPrice", "0")
        self.orig_qty: str = raw.get("origQty", "0")
        self.executed_qty: str = raw.get("executedQty", "0")
        self.time_in_force: str = raw.get("timeInForce", "")
        self.update_time: int = raw.get("updateTime", 0)

    def is_filled(self) -> bool:
        return self.status == "FILLED"

    def summary(self) -> str:
        lines = [
            "─" * 50,
            "  ORDER RESPONSE",
            "─" * 50,
            f"  Order ID      : {self.order_id}",
            f"  Symbol        : {self.symbol}",
            f"  Side          : {self.side}",
            f"  Type          : {self.order_type}",
            f"  Status        : {self.status}",
            f"  Orig Qty      : {self.orig_qty}",
            f"  Executed Qty  : {self.executed_qty}",
            f"  Avg Price     : {self.avg_price}",
        ]
        if self.order_type == "LIMIT":
            lines.append(f"  Limit Price   : {self.price}")
        if self.time_in_force:
            lines.append(f"  Time-in-Force : {self.time_in_force}")
        lines.append("─" * 50)
        return "\n".join(lines)


def build_order_payload(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: Optional[float] = None,
    stop_price: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Construct the order payload dict for the Binance API.
    Assumes inputs have already been validated and normalised.
    """
    payload: Dict[str, Any] = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
    }

    if order_type == "LIMIT":
        if price is None:
            raise ValueError("Price is required for LIMIT orders.")
        payload["price"] = f"{price:.8f}".rstrip("0").rstrip(".")
        payload["timeInForce"] = "GTC"  # Good Till Cancelled

    elif order_type == "STOP_MARKET":
        if stop_price is None:
            raise ValueError("Stop price is required for STOP_MARKET orders.")
        payload["stopPrice"] = f"{stop_price:.8f}".rstrip("0").rstrip(".")

    return payload


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity,
    price=None,
    stop_price=None,
) -> OrderResult:
    """
    Validate inputs, build payload, call the API, and return an OrderResult.

    Raises:
        ValueError: on invalid inputs
        BinanceAPIError: on API-level failures
        requests.exceptions.*: on network failures
    """
    # Validate
    params = validate_all(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price,
    )

    # Build payload
    payload = build_order_payload(**params)

    logger.info(
        "Order request → %s %s %s qty=%s%s",
        params["side"],
        params["symbol"],
        params["order_type"],
        params["quantity"],
        f" @ {params['price']}" if params["price"] else "",
    )

    # Call API
    raw_response = client.place_order(**payload)

    result = OrderResult(raw_response)
    logger.info(
        "Order response → orderId=%s status=%s executedQty=%s avgPrice=%s",
        result.order_id,
        result.status,
        result.executed_qty,
        result.avg_price,
    )
    return result
