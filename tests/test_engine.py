from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from alpha_signal_generator.engine import SignalEngine
from alpha_signal_generator.models import MarketBar
from alpha_signal_generator.pipeline import run_signal_pipeline
from alpha_signal_generator.strategies.rsi_mean_reversion import RsiMeanReversionStrategy


def _bars_with_rsi() -> list[MarketBar]:
    values = [55.0, 48.0, 42.0, 28.0, 24.0, 32.0, 45.0, 52.0, 58.0, 63.0]
    bars: list[MarketBar] = []
    for index, rsi in enumerate(values):
        close = 100.0 + index
        bars.append(
            MarketBar(
                symbol="BTCUSDT",
                open=close,
                high=close + 1.0,
                low=close - 1.0,
                close=close,
                volume=10.0,
                event_time=datetime(2024, 1, 1, 12, index, tzinfo=UTC),
                indicators={"rsi": rsi},
            )
        )
    return bars


def test_engine_emits_entry_and_exit() -> None:
    engine = SignalEngine([RsiMeanReversionStrategy()])
    events = engine.run(_bars_with_rsi())
    actions = [event.action.value for event in events]
    assert "enter" in actions
    assert "exit" in actions


def test_pipeline_with_sample_file() -> None:
    root = Path(__file__).resolve().parents[1]
    sample = root / "samples" / "btcusdt_candles_with_indicators.jsonl"
    signals = run_signal_pipeline(
        candles_path=str(sample),
        strategy_name="rsi_mean_reversion",
        symbol="BTCUSDT",
    )
    assert signals
    assert signals[0]["strategy_id"] == "rsi_mean_reversion"
