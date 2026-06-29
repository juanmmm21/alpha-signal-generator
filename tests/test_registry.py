from __future__ import annotations

import pytest

from alpha_signal_generator.registry import create_strategy


def test_create_strategy_unknown() -> None:
    with pytest.raises(ValueError):
        create_strategy("unknown")


def test_create_strategy_rsi() -> None:
    strategy = create_strategy("rsi_mean_reversion")
    assert strategy.strategy_id == "rsi_mean_reversion"
