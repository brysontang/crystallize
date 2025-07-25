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
    for hyp_table in _build_hypothesis_tables(result):
        log.write(hyp_table)
    if result.errors:
        log.write("[bold red]Errors occurred[/]")
        for cond, err in result.errors.items():
            log.write(f"{cond}: {err}")


def _write_summary(log: RichLog, result: Any) -> None:
    if isinstance(result, dict):
        for name, res in result.items():
            has_table = _build_experiment_table(res) is not None or bool(res.metrics.hypotheses)
            has_errors = bool(res.errors)

            if has_table or has_errors:
                log.write(Text(name, style="bold underline"))
                _write_experiment_summary(log, res)
    else:
        _write_experiment_summary(log, result)
