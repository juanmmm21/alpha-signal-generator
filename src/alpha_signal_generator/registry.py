from __future__ import annotations

from collections.abc import Callable

from alpha_signal_generator.protocols import TradingStrategy
from alpha_signal_generator.strategies import (
    MacdCrossoverStrategy,
    OrderBookImbalanceStrategy,
    RsiMeanReversionStrategy,
)

STRATEGY_REGISTRY: dict[str, Callable[[], TradingStrategy]] = {
    "rsi_mean_reversion": RsiMeanReversionStrategy,
    "macd_crossover": MacdCrossoverStrategy,
    "book_imbalance": OrderBookImbalanceStrategy,
}


def create_strategy(strategy_name: str) -> TradingStrategy:
    if strategy_name not in STRATEGY_REGISTRY:
        supported = ", ".join(sorted(STRATEGY_REGISTRY))
        raise ValueError(f"unsupported strategy: {strategy_name}. supported: {supported}")
    strategy_cls = STRATEGY_REGISTRY[strategy_name]
    return strategy_cls()
