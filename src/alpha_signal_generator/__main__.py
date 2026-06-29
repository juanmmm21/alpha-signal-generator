from __future__ import annotations

import argparse
import json
import logging

from alpha_signal_generator.pipeline import run_signal_pipeline
from alpha_signal_generator.registry import STRATEGY_REGISTRY


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Motor de estrategias que emite señales estrictas de entrada y salida.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Evalúa una estrategia sobre velas JSONL.")
    run.add_argument("--candles", required=True, help="Archivo JSON Lines con velas OHLCV.")
    run.add_argument("--symbol", required=True)
    run.add_argument(
        "--strategy",
        required=True,
        choices=sorted(STRATEGY_REGISTRY),
    )
    run.add_argument("--books", default=None, help="Archivo JSON Lines con métricas de libro.")
    run.add_argument("--output", default=None, help="Archivo JSON de salida opcional.")

    list_strategies = subparsers.add_parser("list", help="Lista estrategias disponibles.")
    list_strategies.add_argument("--json", action="store_true")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    if args.command == "list":
        names = sorted(STRATEGY_REGISTRY)
        if args.json:
            print(json.dumps(names, indent=2))
        else:
            for name in names:
                print(name)
        return

    if args.command == "run":
        signals = run_signal_pipeline(
            candles_path=args.candles,
            strategy_name=args.strategy,
            symbol=args.symbol,
            books_path=args.books,
        )
        rendered = json.dumps(signals, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(rendered)
                handle.write("\n")
            logging.getLogger(__name__).info("wrote %s signals to %s", len(signals), args.output)
            return
        print(rendered)
        return

    raise RuntimeError(f"unsupported command: {args.command}")


if __name__ == "__main__":
    main()
