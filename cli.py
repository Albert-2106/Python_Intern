#!/usr/bin/env python3
"""
Binance Futures Testnet Trading Bot — CLI entry point.

Usage examples:
  python cli.py place --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
  python cli.py place --symbol BTCUSDT --side SELL --type LIMIT --qty 0.001 --price 50000
  python cli.py place --symbol ETHUSDT --side BUY --type STOP_MARKET --qty 0.01 --stop-price 3000
  python cli.py orders --symbol BTCUSDT
  python cli.py account
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional

from bot.client import BinanceAPIError, BinanceClient
from bot.logging_config import get_logger, setup_logging
from bot.orders import place_order

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_credentials() -> tuple[str, str]:
    """Read API credentials from env vars."""
    api_key = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()
    if not api_key or not api_secret:
        print(
            "\n[ERROR] Missing credentials.\n"
            "  Set environment variables before running:\n"
            "    export BINANCE_API_KEY=<your_key>\n"
            "    export BINANCE_API_SECRET=<your_secret>\n",
            file=sys.stderr,
        )
        sys.exit(1)
    return api_key, api_secret


def _print_order_summary(params: dict) -> None:
    print("\n" + "─" * 50)
    print("  ORDER REQUEST SUMMARY")
    print("─" * 50)
    for k, v in params.items():
        print(f"  {k:<15} {v}")
    print("─" * 50)


def _print_order_result(result: dict) -> None:
    print("\n  ORDER RESPONSE")
    print("─" * 50)
    fields = [
        ("orderId",     "Order ID"),
        ("symbol",      "Symbol"),
        ("side",        "Side"),
        ("type",        "Type"),
        ("origQty",     "Quantity"),
        ("executedQty", "Executed Qty"),
        ("avgPrice",    "Avg Price"),
        ("price",       "Price"),
        ("stopPrice",   "Stop Price"),
        ("status",      "Status"),
        ("timeInForce", "Time In Force"),
    ]
    for key, label in fields:
        val = result.get(key)
        if val not in (None, "", "0", "0.00000000"):
            print(f"  {label:<16} {val}")
    print("─" * 50)


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------

def cmd_place(args: argparse.Namespace, client: BinanceClient, logger) -> int:
    """Handle the 'place' sub-command."""
    summary = {
        "Symbol":     args.symbol,
        "Side":       args.side,
        "Type":       args.type,
        "Quantity":   args.qty,
        "Price":      args.price if args.price else "—",
        "Stop Price": args.stop_price if args.stop_price else "—",
    }
    _print_order_summary(summary)

    try:
        result = place_order(
            client=client,
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity=args.qty,
            price=args.price,
            stop_price=args.stop_price,
            time_in_force=args.tif,
        )
    except ValueError as exc:
        logger.error("Validation error: %s", exc)
        print(f"\n[VALIDATION ERROR] {exc}", file=sys.stderr)
        return 1
    except BinanceAPIError as exc:
        logger.error("API error: %s", exc)
        print(f"\n[API ERROR] {exc}", file=sys.stderr)
        return 1

    _print_order_result(result)
    print(f"\n  ✓  Order placed successfully! orderId={result['orderId']}\n")
    return 0


def cmd_orders(args: argparse.Namespace, client: BinanceClient, logger) -> int:
    """Handle the 'orders' sub-command — list open orders."""
    symbol: Optional[str] = args.symbol if args.symbol else None
    try:
        orders = client.get_open_orders(symbol=symbol)
    except BinanceAPIError as exc:
        logger.error("API error fetching open orders: %s", exc)
        print(f"\n[API ERROR] {exc}", file=sys.stderr)
        return 1

    if not orders:
        print("\n  No open orders.\n")
        return 0

    print(f"\n  OPEN ORDERS ({len(orders)} found)")
    print("─" * 50)
    for o in orders:
        print(
            f"  orderId={o.get('orderId')}  {o.get('symbol')}  "
            f"{o.get('side')} {o.get('type')}  qty={o.get('origQty')}  "
            f"price={o.get('price')}  status={o.get('status')}"
        )
    print("─" * 50 + "\n")
    return 0


def cmd_account(args: argparse.Namespace, client: BinanceClient, logger) -> int:
    """Handle the 'account' sub-command — show USDT balance."""
    try:
        account = client.get_account()
    except BinanceAPIError as exc:
        logger.error("API error fetching account: %s", exc)
        print(f"\n[API ERROR] {exc}", file=sys.stderr)
        return 1

    assets = account.get("assets", [])
    print("\n  ACCOUNT BALANCES (non-zero)")
    print("─" * 50)
    for a in assets:
        wb = float(a.get("walletBalance", 0))
        ub = float(a.get("unrealizedProfit", 0))
        if wb or ub:
            print(f"  {a.get('asset'):<10} wallet={wb:.4f}  unrealizedPnL={ub:.4f}")
    print("─" * 50 + "\n")
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Binance Futures Testnet Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Console log verbosity (default: INFO).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # ---- place ----
    p_place = sub.add_parser("place", help="Place a new futures order.")
    p_place.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    p_place.add_argument(
        "--side", required=True, choices=["BUY", "SELL"], help="Order side."
    )
    p_place.add_argument(
        "--type",
        required=True,
        choices=["MARKET", "LIMIT", "STOP_MARKET"],
        help="Order type.",
    )
    p_place.add_argument("--qty", required=True, type=float, help="Order quantity.")
    p_place.add_argument(
        "--price", type=float, default=None, help="Limit price (required for LIMIT)."
    )
    p_place.add_argument(
        "--stop-price",
        dest="stop_price",
        type=float,
        default=None,
        help="Stop trigger price (required for STOP_MARKET).",
    )
    p_place.add_argument(
        "--tif",
        default="GTC",
        choices=["GTC", "IOC", "FOK"],
        help="Time-in-force for LIMIT orders (default: GTC).",
    )

    # ---- orders ----
    p_orders = sub.add_parser("orders", help="List open orders.")
    p_orders.add_argument("--symbol", default=None, help="Filter by symbol.")

    # ---- account ----
    sub.add_parser("account", help="Show account balances.")

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    logger = setup_logging(level=args.log_level)
    logger.info("Trading bot started | command=%s", args.command)

    api_key, api_secret = _get_credentials()
    client = BinanceClient(api_key=api_key, api_secret=api_secret)

    try:
        if args.command == "place":
            exit_code = cmd_place(args, client, logger)
        elif args.command == "orders":
            exit_code = cmd_orders(args, client, logger)
        elif args.command == "account":
            exit_code = cmd_account(args, client, logger)
        else:
            parser.print_help()
            exit_code = 0
    finally:
        client.close()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
