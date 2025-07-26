"""Helper utilities for formatting CLI output."""

from __future__ import annotations

from typing import Any, Optional

from rich.table import Table
from rich.text import Text
from textual.widgets import RichLog


def _build_experiment_table(result: Any) -> Optional[Table]:
    metrics = result.metrics
    treatments = list(metrics.treatments.keys())
    table = Table(title="Metrics", border_style="bright_magenta", expand=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Baseline", style="magenta")
    for t in treatments:
        table.add_column(t, style="green")
    metric_names = set(metrics.baseline.metrics)
    if not metric_names:
        return None
    for t in treatments:
        metric_names.update(metrics.treatments[t].metrics)
    for name in sorted(metric_names):
        row = [name, str(metrics.baseline.metrics.get(name))]
        for t in treatments:
            row.append(str(metrics.treatments[t].metrics.get(name)))
        table.add_row(*row)
    return table


def _build_hypothesis_tables(result: Any) -> list[Table]:
    tables: list[Table] = []
    for hyp in result.metrics.hypotheses:
        treatments = list(hyp.results.keys())
        metric_names = set()
        for res in hyp.results.values():
            metric_names.update(res)

        table = Table(
            title=f"Hypothesis: {hyp.name}",
            border_style="bright_cyan",
            expand=True,
        )
        table.add_column("Treatment", style="magenta")
        for m in sorted(metric_names):
            table.add_column(m, style="green")
        for t in treatments:
            row = [t]
            for m in sorted(metric_names):
                row.append(str(hyp.results[t].get(m)))
            table.add_row(*row)
        if hyp.ranking:
            ranking = ", ".join(f"{k}: {v}" for k, v in hyp.ranking.items())
            table.caption = ranking
        tables.append(table)
    return tables


def _write_experiment_summary(log: RichLog, result: Any) -> None:
    table = _build_experiment_table(result)
    if table:
        log.write(table)
        log.write("\n")
    for hyp_table in _build_hypothesis_tables(result):
        log.write(hyp_table)
        log.write("\n")
    if result.errors:
        log.write("[bold red]Errors occurred[/]")
        for cond, err in result.errors.items():
            log.write(f"{cond}: {err}")


def _write_summary(log: RichLog, result: Any) -> None:
    if isinstance(result, dict):
        for name, res in result.items():
            has_table = _build_experiment_table(res) is not None or bool(
                res.metrics.hypotheses
            )
            has_errors = bool(res.errors)

            if has_table or has_errors:
                log.write(Text(name, style="bold underline"))
                _write_experiment_summary(log, res)
    else:
        _write_experiment_summary(log, result)


import yaml
from pathlib import Path


class IndentDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def create_experiment_scaffolding(
    name: str,
    *,
    directory: Path = Path("experiments"),
    steps: bool = True,
    datasources: bool = True,
    outputs: bool = False,
    hypotheses: bool = False,
    examples: bool = False,
) -> Path:
    """Create a new experiment folder with optional example code."""

    if not name or not name.islower() or " " in name:
        raise ValueError("name must be lowercase and contain no spaces")
    directory.mkdir(exist_ok=True)
    exp_dir = directory / name
    if exp_dir.exists():
        raise FileExistsError(exp_dir)
    exp_dir.mkdir()

    config: dict[str, Any] = {"name": name, "datasource": {}, "steps": []}
    if outputs:
        config["outputs"] = {}
    if hypotheses:
        config["hypotheses"] = []

    if examples:
        if datasources:
            config["datasource"] = {"numbers": "numbers"}
        if steps:
            config["steps"] = ["add_one"]
        if outputs:
            config["outputs"] = {"out": {"file_name": "out.txt"}}
        if hypotheses:
            config["hypotheses"] = [
                {"name": "h", "verifier": "always_sig", "metrics": "val"}
            ]
            config["treatments"] = {
                "add_one": {"delta": 1},
                "add_two": {"delta": 2},
            }

    with open(exp_dir / "config.yaml", "w") as f:
        yaml.dump(config, f, Dumper=IndentDumper, sort_keys=False)

    if datasources:
        ds_code = "from crystallize import data_source\n"
        if examples:
            ds_code += "\n@data_source\ndef numbers(ctx):\n    return 1\n"
        (exp_dir / "datasources.py").write_text(ds_code)

    if steps:
        st_code = "from crystallize import pipeline_step"
        if examples and outputs:
            st_code += ", Artifact"
        st_code += "\nfrom crystallize.utils.context import FrozenContext\n"
        if examples:
            if outputs:
                st_code += "\n@pipeline_step()\ndef add_one(data: int, out: Artifact, delta: int = 1) -> dict:\n    val = data + delta\n    out.write(str(val).encode())\n    return val, {'val': val}\n"
            else:
                st_code += "\n@pipeline_step()\ndef add_one(data: int, delta: int = 1) -> dict:\n    val = data + delta\n    return val, {'val': val}\n"
        (exp_dir / "steps.py").write_text(st_code)

    if outputs:
        out_code = ""
        if examples:
            out_code = ""
        (exp_dir / "outputs.py").write_text(out_code)

    if hypotheses:
        hyp_code = "from crystallize import verifier\n"
        if examples:
            hyp_code += "\n@verifier\ndef always_sig(baseline, treatment):\n    return {'p_value': 0.01, 'significant': True}\n"
        (exp_dir / "hypotheses.py").write_text(hyp_code)

    (exp_dir / "main.py").write_text(
        "from pathlib import Path\n"
        "from crystallize.experiments.experiment import Experiment\n"
        "\n"
        "exp = Experiment.from_yaml(Path(__file__).parent / 'config.yaml')\n"
    )

    return exp_dir
