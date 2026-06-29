from __future__ import annotations

from alpha_signal_generator.base import BaseStrategy
from alpha_signal_generator.models import SignalEvent, SignalSide, StrategyContext


class MacdCrossoverStrategy(BaseStrategy):
    """Entra en largo cuando la línea MACD cruza por encima de la señal."""

    def __init__(
        self,
        strategy_id: str = "macd_crossover",
        macd_key: str = "macd_line",
        signal_key: str = "signal_line",
    ) -> None:
        super().__init__(strategy_id)
        self._macd_key = macd_key
        self._signal_key = signal_key

    def evaluate(self, context: StrategyContext) -> SignalEvent:
        bar = context.bar
        macd = self._indicator(context, self._macd_key)
        signal = self._indicator(context, self._signal_key)
        prev_macd = self._previous_indicator(context, self._macd_key)
        prev_signal = self._previous_indicator(context, self._signal_key)

        if macd is None or signal is None:
            return self._hold(bar, "macd indicators unavailable")

        if context.open_position is SignalSide.LONG:
            bearish_cross = (
                prev_macd is not None
                and prev_signal is not None
                and macd < signal
                and prev_macd >= prev_signal
            )
            if bearish_cross:
                return self._exit(
                    bar,
                    SignalSide.LONG,
                    0.85,
                    "macd crossed below signal line",
                )
            return self._hold(bar, "holding long while macd remains supportive")

        if context.open_position is SignalSide.SHORT:
            return self._hold(bar, "strategy only manages long positions")

        if prev_macd is None or prev_signal is None:
            return self._hold(bar, "waiting for previous macd values")

        if prev_macd <= prev_signal and macd > signal:
            spread = abs(macd - signal)
            confidence = min(1.0, spread / max(abs(signal), 1e-6))
            return self._enter(
                bar,
                SignalSide.LONG,
                confidence,
                "macd crossed above signal line",
            )

        return self._hold(bar, "no macd crossover detected")
