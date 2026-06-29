# alpha-signal-generator

Motor de **estrategias desacopladas** que analiza velas OHLCV, indicadores técnicos y métricas opcionales del libro de órdenes para emitir eventos estrictos de entrada y salida. Quinto módulo del ecosistema [quant-core-infra](https://github.com/juanmmm21/quant-core-infra).

Repositorio: [github.com/juanmmm21/alpha-signal-generator](https://github.com/juanmmm21/alpha-signal-generator)

---

## Qué es y qué problema resuelve

Un bot de trading necesita traducir datos de mercado en decisiones discretas: entrar, salir o mantener. Mezclar esa lógica con ingesta de datos, ejecución de órdenes o backtesting produce código frágil e imposible de testear.

Este módulo aísla la **lógica de decisión** detrás de un contrato claro:

- Cada estrategia implementa `evaluate(context) → SignalEvent`
- El motor mantiene el estado de posición por estrategia
- La salida es un evento tipado con acción, lado, confianza y razón

Añadir una estrategia nueva = una clase + registro en `registry.py`. No hay que tocar el engine ni el pipeline.

---

## Rol en quant-core-infra

```text
market-data-lakehouse ──┐
ta-indicators-from-scratch ──► velas + indicadores ──► alpha-signal-generator
order-book-reconstructor ──┘         (métricas libro)         │
                                                               ▼
                                                    event-driven-backtester
```

Es el **cerebro de decisión** entre el análisis de datos y la simulación/ejecución.

---

## Objetivo

Demuestra:

- Diseño desacoplado con `Protocol` y clase base abstracta
- Contratos estrictos `SignalEvent` para sistemas downstream
- Contexto multi-fuente (velas, indicadores, libro)
- Ingesta JSONL compatible con módulos upstream

---

## Estrategias incluidas

| ID | Lógica de entrada | Lógica de salida |
|----|-------------------|------------------|
| `rsi_mean_reversion` | RSI ≤ umbral sobrevendido (30) | RSI ≥ neutral (50) o sobrecomprado (70) |
| `macd_crossover` | MACD cruza por encima de señal | MACD cruza por debajo de señal |
| `book_imbalance` | Imbalance bid-heavy + spread estrecho | Imbalance cae bajo umbral de salida |

Todas gestionan posiciones **long** en esta versión inicial.

---

## Cómo funciona

1. **Ingesta:** se cargan velas JSONL con campos OHLCV + indicadores opcionales.
2. **Contexto:** por cada barra se construye `StrategyContext` con barra actual, anterior, posición abierta y libro opcional.
3. **Evaluación:** cada estrategia registrada produce un `SignalEvent`.
4. **Estado:** `SignalEngine` actualiza posición interna en `enter` / `exit`.
5. **Salida:** el pipeline filtra eventos `hold` y serializa solo señales accionables.

### Contrato `SignalEvent`

| Campo | Valores | Descripción |
|-------|---------|-------------|
| `action` | `enter`, `exit`, `hold` | Decisión de la estrategia |
| `side` | `long`, `short`, `null` | Requerido en enter/exit |
| `confidence` | `0.0 – 1.0` | Convicción de la señal |
| `reason` | `str` | Texto auditable de la decisión |
| `reference_price` | `Decimal` | Precio de referencia (cierre de barra) |

---

## Arquitectura

```text
Candles + indicators (JSONL)
        │
        ├─ optional book metrics (JSONL)
        ▼
StrategyContext (bar, previous_bar, position, book)
        │
        ▼
SignalEngine
   ├─ RsiMeanReversionStrategy
   ├─ MacdCrossoverStrategy
   └─ OrderBookImbalanceStrategy
        │
        ▼
SignalEvent
```

### Componentes

| Módulo | Responsabilidad |
|--------|----------------|
| `base.py` | `BaseStrategy` con helpers `_enter`, `_exit`, `_hold` |
| `protocols.py` | `TradingStrategy` protocol |
| `strategies/` | Implementaciones concretas |
| `engine.py` | Estado de posición y evaluación barra a barra |
| `registry.py` | Factory `create_strategy(name)` |
| `ingest.py` / `pipeline.py` | JSONL → señales serializadas |

### Decisiones técnicas

- **Decimal** para precios de referencia y métricas de libro
- **float** para indicadores TA (producidos upstream)
- **Una posición por estrategia** — sin netting entre estrategias
- **Salida accionable** — `hold` no aparece en el JSON del pipeline

---

## Cómo añadir una estrategia

```python
from alpha_signal_generator.base import BaseStrategy
from alpha_signal_generator.models import SignalEvent, StrategyContext
from alpha_signal_generator.registry import STRATEGY_REGISTRY


class MyStrategy(BaseStrategy):
    def evaluate(self, context: StrategyContext) -> SignalEvent:
        # tu lógica aquí
        return self._hold(context.bar, "waiting for setup")


STRATEGY_REGISTRY["my_strategy"] = MyStrategy
```

---

## Requisitos

- Python **3.11+**

---

## Instalación

```bash
cd alpha-signal-generator
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Uso CLI

```bash
# Listar estrategias
alpha-signal-generator list

# RSI mean reversion
alpha-signal-generator run \
  --candles samples/btcusdt_candles_with_indicators.jsonl \
  --symbol BTCUSDT \
  --strategy rsi_mean_reversion

# Con confirmación de libro de órdenes
alpha-signal-generator run \
  --candles samples/btcusdt_candles_with_indicators.jsonl \
  --books samples/btcusdt_book_metrics.jsonl \
  --symbol BTCUSDT \
  --strategy book_imbalance \
  --output signals.json
```

---

## Formatos JSONL

### Velas con indicadores

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

Los campos extra (`rsi`, `macd_line`, etc.) se parsean automáticamente como indicadores.

### Métricas de libro

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

## Uso programático

```python
from alpha_signal_generator import (
    MacdCrossoverStrategy,
    RsiMeanReversionStrategy,
    SignalEngine,
    run_signal_pipeline,
)

# Pipeline completo desde archivos
signals = run_signal_pipeline(
    candles_path="candles.jsonl",
    strategy_name="macd_crossover",
    symbol="BTCUSDT",
)

# Motor manual con múltiples estrategias
engine = SignalEngine([
    RsiMeanReversionStrategy(),
    MacdCrossoverStrategy(),
])
```

---

## Desarrollo

```bash
pytest -q
ruff check src tests
mypy src
```

---

## Roadmap

- [ ] Estrategias short y hedging
- [ ] Composición de estrategias (voting, ponderación)
- [ ] Integración en tiempo real con stream de velas

---

## Licencia

MIT
