from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from alpha_signal_generator.models import MarketBar, OrderBookMetrics, SignalAction, StrategyContext
from alpha_signal_generator.strategies.book_imbalance import OrderBookImbalanceStrategy


def _context(imbalance: float, spread: str = "0.10") -> StrategyContext:
    bar = MarketBar(
        symbol="BTCUSDT",
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.5,
        volume=10.0,
        event_time=datetime(2024, 1, 1, 12, 0, tzinfo=UTC),
        indicators={},
    )
    book = OrderBookMetrics(
        symbol="BTCUSDT",
        best_bid=Decimal("100.4"),
        best_ask=Decimal("100.6"),
        spread=Decimal(spread),
        mid_price=Decimal("100.5"),
        bid_depth=Decimal("12"),
        ask_depth=Decimal("8"),
        imbalance=imbalance,
        event_time=datetime(2024, 1, 1, 12, 0, tzinfo=UTC),
    )
    return StrategyContext(bar=bar, bar_index=0, open_position=None, book=book)


def test_book_imbalance_enters_on_bid_pressure() -> None:
    strategy = OrderBookImbalanceStrategy()
    event = strategy.evaluate(_context(0.35))
    assert event.action is SignalAction.ENTER


def test_book_imbalance_holds_without_book() -> None:
    strategy = OrderBookImbalanceStrategy()
    context = StrategyContext(
        bar=_context(0.35).bar,
        bar_index=0,
        open_position=None,
        book=None,
    )
    event = strategy.evaluate(context)
    assert event.action is SignalAction.HOLD
