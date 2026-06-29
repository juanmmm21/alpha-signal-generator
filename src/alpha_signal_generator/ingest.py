from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from alpha_signal_generator.models import (
    MarketBar,
    OrderBookMetrics,
    decimal_from_value,
    parse_indicator_map,
    utc_from_iso8601,
)


def load_market_bars(path: str | Path, default_symbol: str) -> list[MarketBar]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"candle file not found: {file_path}")

    bars: list[MarketBar] = []
    with file_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid json on line {line_number}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"line {line_number} must contain a JSON object")
            bars.append(parse_market_bar(payload, default_symbol))

    if not bars:
        raise ValueError("candle file is empty")
    return bars


def load_order_book_metrics(path: str | Path, default_symbol: str) -> list[OrderBookMetrics]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"order book file not found: {file_path}")

    books: list[OrderBookMetrics] = []
    with file_path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid json on line {line_number}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"line {line_number} must contain a JSON object")
            books.append(parse_order_book_metrics(payload, default_symbol))

    if not books:
        raise ValueError("order book file is empty")
    return books


def parse_market_bar(payload: dict[str, Any], default_symbol: str) -> MarketBar:
    required = ("open", "high", "low", "close", "volume", "event_time")
    for field in required:
        if field not in payload:
            raise ValueError(f"missing required field: {field}")

    symbol = str(payload.get("symbol", default_symbol))
    if not symbol:
        raise ValueError("symbol must not be empty")

    return MarketBar(
        symbol=symbol,
        open=float(payload["open"]),
        high=float(payload["high"]),
        low=float(payload["low"]),
        close=float(payload["close"]),
        volume=float(payload["volume"]),
        event_time=utc_from_iso8601(str(payload["event_time"])),
        indicators=parse_indicator_map(payload),
    )


def parse_order_book_metrics(payload: dict[str, Any], default_symbol: str) -> OrderBookMetrics:
    required = (
        "best_bid",
        "best_ask",
        "spread",
        "mid_price",
        "bid_depth",
        "ask_depth",
        "imbalance",
        "event_time",
    )
    for field in required:
        if field not in payload:
            raise ValueError(f"missing required field: {field}")

    symbol = str(payload.get("symbol", default_symbol))
    if not symbol:
        raise ValueError("symbol must not be empty")

    return OrderBookMetrics(
        symbol=symbol,
        best_bid=decimal_from_value(payload["best_bid"], "best_bid"),
        best_ask=decimal_from_value(payload["best_ask"], "best_ask"),
        spread=decimal_from_value(payload["spread"], "spread"),
        mid_price=decimal_from_value(payload["mid_price"], "mid_price"),
        bid_depth=decimal_from_value(payload["bid_depth"], "bid_depth"),
        ask_depth=decimal_from_value(payload["ask_depth"], "ask_depth"),
        imbalance=float(payload["imbalance"]),
        event_time=utc_from_iso8601(str(payload["event_time"])),
    )
