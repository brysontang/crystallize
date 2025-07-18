from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .yaml_loader import load_experiment_from_file
from rich.console import Console
from rich.table import Table


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

        console = Console()
        table = Table(title="Hypothesis Results")
        table.add_column("Hypothesis", style="cyan")
        table.add_column("Treatment", style="magenta")
        table.add_column("P-Value", justify="right", style="green")
        table.add_column("Significant", justify="center")

        for hyp in result.metrics.hypotheses:
            for treatment_name, res in hyp.results.items():
                p_val = res.get("p_value")
                p_str = f"{p_val:.4f}" if isinstance(p_val, (int, float)) else "N/A"
                sig = res.get("significant")
                sig_str = "[bold green]Yes[/]" if sig else "[bold red]No[/]"
                table.add_row(hyp.name, treatment_name, p_str, sig_str)

        console.print(table)


if __name__ == "__main__":
    main()
