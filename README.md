# alpha-signal-generator

Pluggable **strategy engine** that analyzes OHLCV candles and optional order book metrics to emit strict entry and exit signals. Fifth module of the [quant-core-infra](https://github.com/juanmmm21/quant-core-infra) ecosystem.

Repository: [github.com/juanmmm21/alpha-signal-generator](https://github.com/juanmmm21/alpha-signal-generator)

---

## Objective

This project demonstrates:

- Decoupled strategy design via abstract base classes and protocols
- Strict `SignalEvent` contracts for downstream execution systems
- Multi-source market context (candles, indicators, order book imbalance)
- JSONL ingestion compatible with `market-data-lakehouse` and `ta-indicators-from-scratch`

---

## Built-in strategies

| Strategy ID | Logic |
|-------------|-------|
| `rsi_mean_reversion` | Enter long on RSI oversold, exit on neutral/overbought recovery |
| `macd_crossover` | Enter long on MACD bullish cross, exit on bearish cross |
| `book_imbalance` | Enter long on bid-heavy order book imbalance with spread filter |

Adding a new strategy means implementing `BaseStrategy.evaluate()` and registering it in `registry.py`.

---

## Architecture

```text
Candles + indicators (JSONL)
        │
        ├─ optional order book metrics (JSONL)
        ▼
MarketBar / OrderBookMetrics
        │
        ▼
SignalEngine
   ├─ RsiMeanReversionStrategy
   ├─ MacdCrossoverStrategy
   └─ OrderBookImbalanceStrategy
        │
        ▼
SignalEvent (enter / exit / hold)
```

### Core components

| Module | Responsibility |
|--------|----------------|
| `models.py` | `SignalEvent`, `MarketBar`, `OrderBookMetrics`, `StrategyContext` |
| `protocols.py` | `TradingStrategy` protocol |
| `base.py` | `BaseStrategy` with signal helpers |
| `strategies/` | Concrete strategy implementations |
| `engine.py` | Position-aware evaluation over bar series |
| `ingest.py` | JSONL parsing for candles and book metrics |
| `pipeline.py` | End-to-end run + serialization |
| `registry.py` | Strategy factory |

### Technical decisions

- **Decimal** for reference prices and order book values
- **float indicators** for TA values produced upstream
- **Per-strategy position state** inside `SignalEngine`
- **Actionable-only output** in batch runs (hold events filtered from pipeline output)

---

## Requirements

- Python **3.11+**

---

## Installation

```bash
cd alpha-signal-generator
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## CLI usage

### List strategies

```bash
alpha-signal-generator list
```

### Run RSI mean reversion

```bash
alpha-signal-generator run \
  --candles samples/btcusdt_candles_with_indicators.jsonl \
  --symbol BTCUSDT \
  --strategy rsi_mean_reversion
```

### Run with order book confirmation

```bash
alpha-signal-generator run \
  --candles samples/btcusdt_candles_with_indicators.jsonl \
  --books samples/btcusdt_book_metrics.jsonl \
  --symbol BTCUSDT \
  --strategy book_imbalance
```

---

## JSONL formats

### Candles with indicators

```json
{
  "open": 100.5,
  "high": 101.0,
  "low": 99.5,
  "close": 100.8,
  "volume": 12.0,
  "event_time": "2024-01-01T12:00:00Z",
  "rsi": 28.5,
  "macd_line": -0.12,
  "signal_line": -0.08
}
```

### Order book metrics

```json
{
  "symbol": "BTCUSDT",
  "best_bid": "100.4",
  "best_ask": "100.6",
  "spread": "0.2",
  "mid_price": "100.5",
  "bid_depth": "12.5",
  "ask_depth": "8.0",
  "imbalance": 0.32,
  "event_time": "2024-01-01T12:00:00Z"
}
```

---

## Programmatic usage

```python
from alpha_signal_generator import (
    MacdCrossoverStrategy,
    SignalEngine,
    run_signal_pipeline,
)

signals = run_signal_pipeline(
    candles_path="candles.jsonl",
    strategy_name="macd_crossover",
    symbol="BTCUSDT",
)

engine = SignalEngine([MacdCrossoverStrategy()])
```

---

## Development

```bash
pytest -q
ruff check src tests
mypy src
```

---

## Ecosystem integration

```text
market-data-lakehouse ──┐
ta-indicators-from-scratch ──► alpha-signal-generator ──► event-driven-backtester
order-book-reconstructor ──┘
```

---

## License

MIT
