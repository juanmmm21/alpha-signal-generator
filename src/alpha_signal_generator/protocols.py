from __future__ import annotations

from typing import Protocol

from alpha_signal_generator.models import SignalEvent, StrategyContext


class TradingStrategy(Protocol):
    """Contrato para estrategias desacopladas que emiten señales estrictas."""

    strategy_id: str

    def evaluate(self, context: StrategyContext) -> SignalEvent:
        ...
