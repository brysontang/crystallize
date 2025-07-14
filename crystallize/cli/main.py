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
        result = experiment.run(
            treatments=experiment.treatments,
            hypotheses=experiment.hypotheses,
            replicates=experiment.replicates,
        )
        hyp_map = {
            h.name: {"results": h.results, "ranking": h.ranking}
            for h in result.metrics.hypotheses
        }
        print(hyp_map)


if __name__ == "__main__":
    main()
