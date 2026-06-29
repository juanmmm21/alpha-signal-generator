from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from alpha_signal_generator.base import BaseStrategy
from alpha_signal_generator.models import SignalEvent, SignalSide, StrategyContext


@dataclass(frozen=True, slots=True)
class BookImbalanceConfig:
    enter_imbalance: float = 0.25
    exit_imbalance: float = 0.05
    max_spread_bps: float = 15.0

    def __post_init__(self) -> None:
        if not 0.0 < self.exit_imbalance < self.enter_imbalance <= 1.0:
            raise ValueError("exit_imbalance must be lower than enter_imbalance")
        if self.max_spread_bps <= 0:
            raise ValueError("max_spread_bps must be positive")


class OrderBookImbalanceStrategy(BaseStrategy):
    """Usa desequilibrio bid/ask y spread para confirmar entradas de momentum."""

    def __init__(
        self,
        strategy_id: str = "book_imbalance",
        config: BookImbalanceConfig | None = None,
    ) -> None:
        super().__init__(strategy_id)
        self._config = config or BookImbalanceConfig()

    def evaluate(self, context: StrategyContext) -> SignalEvent:
        bar = context.bar
        book = context.book
        if book is None:
            return self._hold(bar, "order book metrics unavailable")

        spread_bps = self._spread_bps(book.spread, book.mid_price)

        if context.open_position is SignalSide.LONG:
            if book.imbalance <= self._config.exit_imbalance:
                return self._exit(
                    bar,
                    SignalSide.LONG,
                    0.75,
                    f"book imbalance faded to {book.imbalance:.3f}",
                )
            return self._hold(bar, f"holding long with imbalance {book.imbalance:.3f}")

        if spread_bps > self._config.max_spread_bps:
            return self._hold(bar, f"spread too wide at {spread_bps:.2f} bps")

        if book.imbalance >= self._config.enter_imbalance:
            confidence = min(1.0, book.imbalance)
            return self._enter(
                bar,
                SignalSide.LONG,
                confidence,
                f"bid-heavy imbalance {book.imbalance:.3f}",
            )

        return self._hold(bar, f"insufficient book imbalance {book.imbalance:.3f}")

    @staticmethod
    def _spread_bps(spread: Decimal, mid_price: Decimal) -> float:
        if mid_price <= Decimal("0"):
            raise ValueError("mid_price must be positive")
        ratio = spread / mid_price
        return float(ratio * Decimal("10000"))
