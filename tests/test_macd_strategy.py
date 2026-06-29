from __future__ import annotations

from datetime import UTC, datetime

from alpha_signal_generator.models import MarketBar, SignalAction, SignalSide, StrategyContext
from alpha_signal_generator.strategies.macd_crossover import MacdCrossoverStrategy


def _bar(macd: float, signal: float, close: float = 100.0) -> MarketBar:
    return MarketBar(
        symbol="BTCUSDT",
        open=close,
        high=close + 1.0,
        low=close - 1.0,
        close=close,
        volume=10.0,
        event_time=datetime(2024, 1, 1, 12, 0, tzinfo=UTC),
        indicators={"macd_line": macd, "signal_line": signal},
    )


def test_macd_strategy_enters_on_bullish_cross() -> None:
    strategy = MacdCrossoverStrategy()
    previous = _bar(-0.2, -0.1)
    current = _bar(0.1, 0.0)
    context = StrategyContext(
        bar=current,
        bar_index=1,
        open_position=None,
        previous_bar=previous,
    )
    event = strategy.evaluate(context)
    assert event.action is SignalAction.ENTER
    assert event.side is SignalSide.LONG


def test_macd_strategy_exits_on_bearish_cross() -> None:
    strategy = MacdCrossoverStrategy()
    previous = _bar(0.2, 0.1)
    current = _bar(-0.1, 0.0)
    context = StrategyContext(
        bar=current,
        bar_index=2,
        open_position=SignalSide.LONG,
        previous_bar=previous,
    )
    event = strategy.evaluate(context)
    assert event.action is SignalAction.EXIT
