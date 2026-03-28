#!/usr/bin/env python3
"""
cli.py — Command-line entry point for the Binance Futures Trading Bot.

Usage examples:
    # Market buy
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01

    # Limit sell
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 100000

    # Stop-Market sell (bonus order type)
    python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.01 --stop-price 85000

    # Load credentials from environment (recommended):
    export BINANCE_API_KEY=your_key
    export BINANCE_API_SECRET=your_secret
"""

import argparse
import os
import sys

import requests

from bot.client import BinanceAPIError, BinanceClient
from bot.logging_config import get_logger
from bot.orders import place_order

logger = get_logger(__name__)

# ── ANSI colour helpers (no extra dependency) ──────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _c(text: str, colour: str) -> str:
    return f"{colour}{text}{RESET}"


# ── Argument parser ────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet (USDT-M) — Trading Bot CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --symbol BTCUSDT --side BUY  --type MARKET     --quantity 0.01
  python cli.py --symbol BTCUSDT --side SELL --type LIMIT       --quantity 0.01 --price 100000
  python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.01 --stop-price 85000

Credentials are read from environment variables:
  BINANCE_API_KEY      your Binance Testnet API key
  BINANCE_API_SECRET   your Binance Testnet API secret
        """,
    )

    parser.add_argument(
        "--symbol", required=True,
        help="Trading pair symbol, e.g. BTCUSDT",
        metavar="SYMBOL",
    )
    parser.add_argument(
        "--side", required=True,
        choices=["BUY", "SELL", "buy", "sell"],
        help="Order side: BUY or SELL",
        metavar="SIDE",
    )
    parser.add_argument(
        "--type", required=True,
        dest="order_type",
        choices=["MARKET", "LIMIT", "STOP_MARKET", "market", "limit", "stop_market"],
        help="Order type: MARKET, LIMIT, or STOP_MARKET",
        metavar="TYPE",
    )
    parser.add_argument(
        "--quantity", required=True,
        help="Order quantity (e.g. 0.01)",
        metavar="QTY",
    )
    parser.add_argument(
        "--price",
        default=None,
        help="Limit price — required for LIMIT orders",
        metavar="PRICE",
    )
    parser.add_argument(
        "--stop-price",
        dest="stop_price",
        default=None,
        help="Stop price — required for STOP_MARKET orders",
        metavar="STOP_PRICE",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Binance API key (overrides BINANCE_API_KEY env var)",
        metavar="KEY",
    )
    parser.add_argument(
        "--api-secret",
        default=None,
        help="Binance API secret (overrides BINANCE_API_SECRET env var)",
        metavar="SECRET",
    )
    return parser


# ── Output helpers ─────────────────────────────────────────────────────────

def print_request_summary(args: argparse.Namespace) -> None:
    print()
    print(_c("─" * 50, CYAN))
    print(_c("  ORDER REQUEST SUMMARY", BOLD + CYAN))
    print(_c("─" * 50, CYAN))
    print(f"  Symbol     : {_c(args.symbol.upper(), BOLD)}")
    print(f"  Side       : {_c(args.side.upper(), BOLD)}")
    print(f"  Type       : {_c(args.order_type.upper(), BOLD)}")
    print(f"  Quantity   : {_c(str(args.quantity), BOLD)}")
    if args.price:
        print(f"  Price      : {_c(str(args.price), BOLD)}")
    if args.stop_price:
        print(f"  Stop Price : {_c(str(args.stop_price), BOLD)}")
    print(_c("─" * 50, CYAN))
    print()


def print_order_result(result) -> None:
    status_colour = GREEN if result.is_filled() else YELLOW
    print()
    print(_c("─" * 50, GREEN))
    print(_c("  ORDER RESPONSE", BOLD + GREEN))
    print(_c("─" * 50, GREEN))
    print(f"  Order ID      : {_c(str(result.order_id), BOLD)}")
    print(f"  Symbol        : {result.symbol}")
    print(f"  Side          : {result.side}")
    print(f"  Type          : {result.order_type}")
    print(f"  Status        : {_c(result.status, status_colour + BOLD)}")
    print(f"  Orig Qty      : {result.orig_qty}")
    print(f"  Executed Qty  : {result.executed_qty}")
    print(f"  Avg Price     : {result.avg_price}")
    if result.order_type == "LIMIT":
        print(f"  Limit Price   : {result.price}")
    if result.time_in_force:
        print(f"  Time-in-Force : {result.time_in_force}")
    print(_c("─" * 50, GREEN))
    print()


# ── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # ── Resolve credentials ──────────────────────────────────────────────
    api_key = args.api_key or os.environ.get("BINANCE_API_KEY", "")
    api_secret = args.api_secret or os.environ.get("BINANCE_API_SECRET", "")

    if not api_key or not api_secret:
        print(
            _c(
                "\n[ERROR] API credentials not found.\n"
                "Set BINANCE_API_KEY and BINANCE_API_SECRET environment variables,\n"
                "or pass --api-key / --api-secret flags.\n",
                RED,
            )
        )
        logger.error("Missing API credentials.")
        sys.exit(1)

    # ── Print request summary ────────────────────────────────────────────
    print_request_summary(args)

    # ── Initialise client ────────────────────────────────────────────────
    client = BinanceClient(api_key=api_key, api_secret=api_secret)

    # ── Place order ──────────────────────────────────────────────────────
    try:
        result = place_order(
            client=client,
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
        )

        print_order_result(result)
        print(_c("  ✅  Order placed successfully!", BOLD + GREEN))
        print()
        logger.info("Order completed successfully. orderId=%s", result.order_id)

    except ValueError as exc:
        print(_c(f"\n  ❌  Validation error: {exc}\n", RED))
        logger.error("Validation error: %s", exc)
        sys.exit(1)

    except BinanceAPIError as exc:
        print(_c(f"\n  ❌  Binance API error [{exc.code}]: {exc.message}\n", RED))
        logger.error("BinanceAPIError: code=%s message=%s", exc.code, exc.message)
        sys.exit(1)

    except requests.exceptions.Timeout:
        print(_c("\n  ❌  Request timed out. Check your network or try again.\n", RED))
        logger.error("Request timed out.")
        sys.exit(1)

    except requests.exceptions.ConnectionError as exc:
        print(_c(f"\n  ❌  Connection failed: {exc}\n", RED))
        logger.error("Connection error: %s", exc)
        sys.exit(1)

    except Exception as exc:
        print(_c(f"\n  ❌  Unexpected error: {exc}\n", RED))
        logger.exception("Unexpected error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
