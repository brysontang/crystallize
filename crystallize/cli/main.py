from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .yaml_loader import load_experiment_from_file


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="crystallize")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run experiment from YAML")
    run_parser.add_argument("config", type=Path, help="Path to experiment YAML")

    args = parser.parse_args(argv)

    if args.command == "run":
        experiment = load_experiment_from_file(args.config)
        experiment.validate()
        result = experiment.run()
        print(result.metrics["hypotheses"])


if __name__ == "__main__":
    main()
