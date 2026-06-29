from __future__ import annotations

from datetime import UTC, datetime

from alpha_signal_generator.models import MarketBar, SignalAction, SignalSide, StrategyContext
from alpha_signal_generator.strategies.rsi_mean_reversion import RsiMeanReversionStrategy


def _bar(close: float, rsi: float) -> MarketBar:
    return MarketBar(
        symbol="BTCUSDT",
        open=close,
        high=close + 1.0,
        low=close - 1.0,
        close=close,
        volume=10.0,
        event_time=datetime(2024, 1, 1, 12, 0, tzinfo=UTC),
        indicators={"rsi": rsi},
    )


def test_rsi_strategy_enters_on_oversold() -> None:
    strategy = RsiMeanReversionStrategy()
    context = StrategyContext(bar=_bar(98.0, 25.0), bar_index=0, open_position=None)
    event = strategy.evaluate(context)
    assert event.action is SignalAction.ENTER
    assert event.side is SignalSide.LONG


def test_rsi_strategy_exits_on_recovery() -> None:
    strategy = RsiMeanReversionStrategy()
    context = StrategyContext(bar=_bar(101.0, 55.0), bar_index=1, open_position=SignalSide.LONG)
    event = strategy.evaluate(context)
    assert event.action is SignalAction.EXIT
    assert event.side is SignalSide.LONG
