from __future__ import annotations

from dataclasses import dataclass

from alpha_signal_generator.base import BaseStrategy
from alpha_signal_generator.models import SignalEvent, SignalSide, StrategyContext


@dataclass(frozen=True, slots=True)
class RsiMeanReversionConfig:
    oversold: float = 30.0
    overbought: float = 70.0
    exit_neutral: float = 50.0
    rsi_key: str = "rsi"

    def __post_init__(self) -> None:
        if not 0.0 < self.oversold < self.overbought < 100.0:
            raise ValueError("oversold and overbought must satisfy 0 < oversold < overbought < 100")
        if not self.oversold < self.exit_neutral < self.overbought:
            raise ValueError("exit_neutral must be between oversold and overbought")


class RsiMeanReversionStrategy(BaseStrategy):
    """Entra en largo con RSI sobrevendido y sale al recuperar neutralidad."""

    def __init__(
        self,
        strategy_id: str = "rsi_mean_reversion",
        config: RsiMeanReversionConfig | None = None,
    ) -> None:
        super().__init__(strategy_id)
        self._config = config or RsiMeanReversionConfig()

    def evaluate(self, context: StrategyContext) -> SignalEvent:
        bar = context.bar
        rsi = self._indicator(context, self._config.rsi_key)
        if rsi is None:
            return self._hold(bar, "rsi indicator unavailable")

        if context.open_position is SignalSide.LONG:
            if rsi >= self._config.exit_neutral:
                confidence = min(1.0, (rsi - self._config.exit_neutral) / 20.0)
                return self._exit(
                    bar,
                    SignalSide.LONG,
                    confidence,
                    f"rsi recovered to {rsi:.2f}",
                )
            if rsi >= self._config.overbought:
                return self._exit(
                    bar,
                    SignalSide.LONG,
                    0.9,
                    f"rsi overbought at {rsi:.2f}",
                )
            return self._hold(bar, f"holding long with rsi {rsi:.2f}")

        if context.open_position is SignalSide.SHORT:
            return self._hold(bar, "strategy only manages long positions")

        if rsi <= self._config.oversold:
            confidence = min(1.0, (self._config.oversold - rsi) / self._config.oversold)
            return self._enter(
                bar,
                SignalSide.LONG,
                confidence,
                f"rsi oversold at {rsi:.2f}",
            )

        return self._hold(bar, f"no entry with rsi {rsi:.2f}")
