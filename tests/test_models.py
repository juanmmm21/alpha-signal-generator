from __future__ import annotations

from datetime import UTC, datetime

import pytest

from alpha_signal_generator.models import MarketBar, SignalAction, SignalEvent


def _bar(close: float, rsi: float | None = None) -> MarketBar:
    indicators = {"rsi": rsi} if rsi is not None else {}
    return MarketBar(
        symbol="BTCUSDT",
        open=close,
        high=close + 1.0,
        low=close - 1.0,
        close=close,
        volume=10.0,
        event_time=datetime(2024, 1, 1, 12, 0, tzinfo=UTC),
        indicators=indicators,
    )


def test_signal_event_requires_side_for_entry() -> None:
    bar = _bar(100.0)
    with pytest.raises(ValueError):
        SignalEvent(
            strategy_id="test",
            symbol=bar.symbol,
            action=SignalAction.ENTER,
            side=None,
            confidence=0.5,
            reason="invalid",
            event_time=bar.event_time,
        )


def test_market_bar_rejects_invalid_high_low() -> None:
    with pytest.raises(ValueError):
        MarketBar(
            symbol="BTCUSDT",
            open=100.0,
            high=90.0,
            low=95.0,
            close=98.0,
            volume=1.0,
            event_time=datetime(2024, 1, 1, tzinfo=UTC),
            indicators={},
        )
