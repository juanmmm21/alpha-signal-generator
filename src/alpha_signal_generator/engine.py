from __future__ import annotations

from alpha_signal_generator.models import (
    MarketBar,
    OrderBookMetrics,
    SignalEvent,
    SignalSide,
    StrategyContext,
)
from alpha_signal_generator.protocols import TradingStrategy


class SignalEngine:
    """Evalúa estrategias sobre una serie temporal y mantiene estado de posición."""

    def __init__(self, strategies: list[TradingStrategy]) -> None:
        if not strategies:
            raise ValueError("strategies must not be empty")
        self._strategies = strategies
        self._positions: dict[str, SignalSide | None] = {
            strategy.strategy_id: None for strategy in strategies
        }

    @property
    def strategies(self) -> tuple[TradingStrategy, ...]:
        return tuple(self._strategies)

    def evaluate_bar(
        self,
        context: StrategyContext,
    ) -> list[SignalEvent]:
        events: list[SignalEvent] = []
        for strategy in self._strategies:
            strategy_context = StrategyContext(
                bar=context.bar,
                bar_index=context.bar_index,
                open_position=self._positions[strategy.strategy_id],
                previous_bar=context.previous_bar,
                book=context.book,
            )
            event = strategy.evaluate(strategy_context)
            self._apply_position(strategy.strategy_id, event)
            events.append(event)
        return events

    def run(
        self,
        bars: list[MarketBar],
        books: list[OrderBookMetrics | None] | None = None,
    ) -> list[SignalEvent]:
        if not bars:
            raise ValueError("bars must not be empty")

        book_series = books or [None] * len(bars)
        if len(book_series) != len(bars):
            raise ValueError("books length must match bars length")

        all_events: list[SignalEvent] = []
        previous_bar: MarketBar | None = None
        for index, (bar, book) in enumerate(zip(bars, book_series, strict=True)):
            context = StrategyContext(
                bar=bar,
                bar_index=index,
                open_position=None,
                previous_bar=previous_bar,
                book=book,
            )
            events = self.evaluate_bar(context)
            actionable = [event for event in events if event.action.value != "hold"]
            all_events.extend(actionable)
            previous_bar = bar
        return all_events

    def _apply_position(self, strategy_id: str, event: SignalEvent) -> None:
        if event.action.value == "enter" and event.side is not None:
            self._positions[strategy_id] = event.side
            return
        if event.action.value == "exit":
            self._positions[strategy_id] = None
