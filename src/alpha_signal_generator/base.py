from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from alpha_signal_generator.models import (
    MarketBar,
    SignalAction,
    SignalEvent,
    SignalSide,
    StrategyContext,
)


class BaseStrategy(ABC):
    """Clase base abstracta para estrategias con helpers de señal consistentes."""

    def __init__(self, strategy_id: str) -> None:
        if not strategy_id:
            raise ValueError("strategy_id must not be empty")
        self.strategy_id = strategy_id

    @abstractmethod
    def evaluate(self, context: StrategyContext) -> SignalEvent:
        ...

    def _hold(self, bar: MarketBar, reason: str) -> SignalEvent:
        return SignalEvent(
            strategy_id=self.strategy_id,
            symbol=bar.symbol,
            action=SignalAction.HOLD,
            side=None,
            confidence=0.0,
            reason=reason,
            event_time=bar.event_time,
            reference_price=Decimal(str(bar.close)),
        )

    def _enter(
        self,
        bar: MarketBar,
        side: SignalSide,
        confidence: float,
        reason: str,
    ) -> SignalEvent:
        return SignalEvent(
            strategy_id=self.strategy_id,
            symbol=bar.symbol,
            action=SignalAction.ENTER,
            side=side,
            confidence=confidence,
            reason=reason,
            event_time=bar.event_time,
            reference_price=Decimal(str(bar.close)),
        )

    def _exit(
        self,
        bar: MarketBar,
        side: SignalSide,
        confidence: float,
        reason: str,
    ) -> SignalEvent:
        return SignalEvent(
            strategy_id=self.strategy_id,
            symbol=bar.symbol,
            action=SignalAction.EXIT,
            side=side,
            confidence=confidence,
            reason=reason,
            event_time=bar.event_time,
            reference_price=Decimal(str(bar.close)),
        )

    @staticmethod
    def _indicator(context: StrategyContext, name: str) -> float | None:
        value = context.bar.indicators.get(name)
        if value is None:
            return None
        return value

    @staticmethod
    def _previous_indicator(context: StrategyContext, name: str) -> float | None:
        if context.previous_bar is None:
            return None
        value = context.previous_bar.indicators.get(name)
        if value is None:
            return None
        return value

    @staticmethod
    def _crossed_above(current: float, previous: float, threshold: float) -> bool:
        return previous <= threshold < current

    @staticmethod
    def _crossed_below(current: float, previous: float, threshold: float) -> bool:
        return previous >= threshold > current
