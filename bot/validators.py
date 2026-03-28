"""
Input validators for trading bot CLI parameters.
All functions raise ValueError with descriptive messages on failure.
"""

from typing import Optional

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


def validate_symbol(symbol: str) -> str:
    """Validate and normalise the trading symbol."""
    if not symbol or not isinstance(symbol, str):
        raise ValueError("Symbol must be a non-empty string (e.g. BTCUSDT).")
    symbol = symbol.strip().upper()
    if len(symbol) < 3:
        raise ValueError(f"Symbol '{symbol}' is too short. Expected something like BTCUSDT.")
    return symbol


def validate_side(side: str) -> str:
    """Validate order side: BUY or SELL."""
    if not side or not isinstance(side, str):
        raise ValueError("Side must be a non-empty string.")
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}.")
    return side


def validate_order_type(order_type: str) -> str:
    """Validate order type: MARKET, LIMIT, or STOP_MARKET."""
    if not order_type or not isinstance(order_type, str):
        raise ValueError("Order type must be a non-empty string.")
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity) -> float:
    """Validate quantity: must be a positive number."""
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(f"Quantity '{quantity}' is not a valid number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be greater than 0. Got: {qty}.")
    return qty


def validate_price(price, order_type: str) -> Optional[float]:
    """
    Validate price.
    - LIMIT / STOP_MARKET: required, must be positive.
    - MARKET: ignored (returns None).
    """
    order_type = order_type.strip().upper()
    if order_type in ("MARKET", "STOP_MARKET"):
        return None  # price is not used for market or stop-market orders

    if price is None:
        raise ValueError(f"Price is required for {order_type} orders.")
    try:
        p = float(price)
    except (TypeError, ValueError):
        raise ValueError(f"Price '{price}' is not a valid number.")
    if p <= 0:
        raise ValueError(f"Price must be greater than 0. Got: {p}.")
    return p


def validate_stop_price(stop_price, order_type: str) -> Optional[float]:
    """Validate stop price — only required for STOP_MARKET orders."""
    order_type = order_type.strip().upper()
    if order_type != "STOP_MARKET":
        return None
    if stop_price is None:
        raise ValueError("Stop price is required for STOP_MARKET orders.")
    try:
        sp = float(stop_price)
    except (TypeError, ValueError):
        raise ValueError(f"Stop price '{stop_price}' is not a valid number.")
    if sp <= 0:
        raise ValueError(f"Stop price must be greater than 0. Got: {sp}.")
    return sp


def validate_all(
    symbol: str,
    side: str,
    order_type: str,
    quantity,
    price=None,
    stop_price=None,
) -> dict:
    """
    Run all validators and return a clean, normalised parameter dict.
    Raises ValueError on the first failure.
    """
    return {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
        "price": validate_price(price, order_type),
        "stop_price": validate_stop_price(stop_price, order_type),
    }
