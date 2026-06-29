from __future__ import annotations

from dataclasses import asdict
from typing import Any

from alpha_signal_generator.engine import SignalEngine
from alpha_signal_generator.ingest import load_market_bars, load_order_book_metrics
from alpha_signal_generator.models import OrderBookMetrics, SignalEvent
from alpha_signal_generator.protocols import TradingStrategy
from alpha_signal_generator.registry import create_strategy


def serialize_signal(event: SignalEvent) -> dict[str, Any]:
    payload = asdict(event)
    payload["action"] = event.action.value
    payload["side"] = event.side.value if event.side is not None else None
    payload["event_time"] = event.event_time.isoformat()
    if event.reference_price is not None:
        payload["reference_price"] = str(event.reference_price)
    return payload


def align_books(
    bar_count: int,
    books: list[OrderBookMetrics] | None,
) -> list[OrderBookMetrics | None] | None:
    if books is None:
        return None
    if len(books) == bar_count:
        return [book for book in books]
    if len(books) == 1:
        return [books[0]] * bar_count
    raise ValueError("order book series must match bar count or provide a single snapshot")


def run_signal_pipeline(
    candles_path: str,
    strategy_name: str,
    symbol: str,
    books_path: str | None = None,
) -> list[dict[str, Any]]:
    bars = load_market_bars(candles_path, default_symbol=symbol)
    books = load_order_book_metrics(books_path, default_symbol=symbol) if books_path else None
    aligned_books = align_books(len(bars), books)

    strategy = create_strategy(strategy_name)
    engine = SignalEngine([strategy])
    events = engine.run(bars, aligned_books)
    return [serialize_signal(event) for event in events]


def run_multi_strategy_pipeline(
    candles_path: str,
    strategies: list[TradingStrategy],
    symbol: str,
    books_path: str | None = None,
) -> list[dict[str, Any]]:
    bars = load_market_bars(candles_path, default_symbol=symbol)
    books = load_order_book_metrics(books_path, default_symbol=symbol) if books_path else None
    aligned_books = align_books(len(bars), books)

    engine = SignalEngine(strategies)
    events = engine.run(bars, aligned_books)
    return [serialize_signal(event) for event in events]
