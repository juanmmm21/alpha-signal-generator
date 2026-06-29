from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any


class SignalSide(StrEnum):
    LONG = "long"
    SHORT = "short"


class SignalAction(StrEnum):
    ENTER = "enter"
    EXIT = "exit"
    HOLD = "hold"


@dataclass(frozen=True, slots=True)
class SignalEvent:
    """Evento estricto de señal emitido por una estrategia."""

    strategy_id: str
    symbol: str
    action: SignalAction
    side: SignalSide | None
    confidence: float
    reason: str
    event_time: datetime
    reference_price: Decimal | None = None

    def __post_init__(self) -> None:
        if not self.strategy_id:
            raise ValueError("strategy_id must not be empty")
        if not self.symbol:
            raise ValueError("symbol must not be empty")
        if not self.reason:
            raise ValueError("reason must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.event_time.tzinfo is None:
            raise ValueError("event_time must be timezone-aware")
        if self.action in {SignalAction.ENTER, SignalAction.EXIT} and self.side is None:
            raise ValueError("side is required for enter and exit actions")
        if self.action is SignalAction.HOLD and self.side is not None:
            raise ValueError("side must be null for hold actions")
        if self.reference_price is not None and self.reference_price <= Decimal("0"):
            raise ValueError("reference_price must be positive when provided")


@dataclass(frozen=True, slots=True)
class MarketBar:
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    event_time: datetime
    indicators: dict[str, float]

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("symbol must not be empty")
        if self.open <= 0 or self.high <= 0 or self.low <= 0 or self.close <= 0:
            raise ValueError("ohlc prices must be positive")
        if self.volume < 0:
            raise ValueError("volume must be non-negative")
        if self.high < self.low:
            raise ValueError("high must be >= low")
        if self.event_time.tzinfo is None:
            raise ValueError("event_time must be timezone-aware")


@dataclass(frozen=True, slots=True)
class OrderBookMetrics:
    symbol: str
    best_bid: Decimal
    best_ask: Decimal
    spread: Decimal
    mid_price: Decimal
    bid_depth: Decimal
    ask_depth: Decimal
    imbalance: float
    event_time: datetime

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("symbol must not be empty")
        if self.best_bid <= Decimal("0") or self.best_ask <= Decimal("0"):
            raise ValueError("best bid and ask must be positive")
        if self.best_ask < self.best_bid:
            raise ValueError("best_ask must be >= best_bid")
        if self.spread < Decimal("0"):
            raise ValueError("spread must be non-negative")
        if self.mid_price <= Decimal("0"):
            raise ValueError("mid_price must be positive")
        if self.bid_depth < Decimal("0") or self.ask_depth < Decimal("0"):
            raise ValueError("depth values must be non-negative")
        if not -1.0 <= self.imbalance <= 1.0:
            raise ValueError("imbalance must be between -1 and 1")
        if self.event_time.tzinfo is None:
            raise ValueError("event_time must be timezone-aware")


@dataclass(frozen=True, slots=True)
class StrategyContext:
    bar: MarketBar
    bar_index: int
    open_position: SignalSide | None
    previous_bar: MarketBar | None = None
    book: OrderBookMetrics | None = None

    def __post_init__(self) -> None:
        if self.bar_index < 0:
            raise ValueError("bar_index must be non-negative")
        if self.book is not None and self.book.symbol != self.bar.symbol:
            raise ValueError("book symbol must match bar symbol")


def utc_from_iso8601(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def parse_indicator_map(payload: dict[str, Any]) -> dict[str, float]:
    reserved = {"open", "high", "low", "close", "volume", "symbol", "event_time"}
    indicators: dict[str, float] = {}
    for key, value in payload.items():
        if key in reserved:
            continue
        if value is None:
            continue
        try:
            parsed = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"indicator {key} must be numeric") from exc
        indicators[key] = parsed
    return indicators


def decimal_from_value(value: object, field_name: str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float, str)):
        return Decimal(str(value))
    raise ValueError(f"{field_name} must be numeric")
