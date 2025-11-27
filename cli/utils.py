"""Helper utilities for formatting CLI output."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from rich.table import Table
from rich.text import Text
from textual.widgets import RichLog


def _build_experiment_table(
    result: Any,
    *,
    highlight: str | None = None,
    inactive: set[str] | None = None,
) -> Optional[Table]:
    metrics = result.metrics
    treatments = list(metrics.treatments.keys())
    if highlight and highlight in treatments:
        treatments.remove(highlight)
        treatments.insert(0, highlight)
    table = Table(title="Metrics", border_style="bright_magenta", expand=True)
    table.add_column("Metric", style="cyan")
    table.add_column("Baseline", style="magenta")
    for t in treatments:
        base = t.rsplit(" (v", 1)[0]
        color = "red" if inactive and base in inactive else "green"
        table.add_column(t, style=color)
    metric_names = set(metrics.baseline.metrics)
    if not metric_names:
        return None
    for t in treatments:
        metric_names.update(metrics.treatments[t].metrics)
    for name in sorted(metric_names):
        row = [name]
        # Truncate baseline value if too long
        baseline_val = str(metrics.baseline.metrics.get(name))
        if len(baseline_val) > 50:
            baseline_val = baseline_val[:47] + "..."
        row.append(baseline_val)

        # Truncate treatment values if too long
        for t in treatments:
            val = str(metrics.treatments[t].metrics.get(name))
            if len(val) > 50:
                val = val[:47] + "..."
            row.append(val)
        table.add_row(*row)
    return table


def _build_artifact_table(result: Any) -> Optional[Table]:
    artifacts = getattr(result, "artifacts", {})
    if not artifacts:
        return None
    treatments: set[str] = set()
    for mapping in artifacts.values():
        treatments.update(mapping.keys())
    order = ["baseline", *sorted(t for t in treatments if t != "baseline")]
    table = Table(title="Artifacts", border_style="bright_blue", expand=True)
    table.add_column("Artifact", style="cyan")
    for t in order:
        label = "Baseline" if t == "baseline" else t
        table.add_column(label, style="magenta" if t == "baseline" else "green")
    for name in sorted(artifacts):
        row: list[Any] = [name]
        mapping = artifacts[name]
        for t in order:
            path = mapping.get(t)
            if path is None:
                row.append("")
            else:
                p = Path(path)
                row.append(Text(str(p), style=f"link {p.resolve().as_uri()}"))
        table.add_row(*row)
    return table


def filter_mapping(mapping: Dict[str, Any], query: str) -> Dict[str, Any]:
    """Return subset of mapping where key contains ``query`` (case-insensitive)."""
    q = query.lower()
    return {k: v for k, v in mapping.items() if q in k.lower()}


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


def _write_experiment_summary(
    log: RichLog,
    result: Any,
    *,
    highlight: str | None = None,
    inactive: set[str] | None = None,
) -> None:
    table = _build_experiment_table(result, highlight=highlight, inactive=inactive)
    if table:
        log.write(table)
        log.write("\n")
    art_table = _build_artifact_table(result)
    if art_table:
        log.write(art_table)
        log.write("\n")
    for hyp_table in _build_hypothesis_tables(result):
        log.write(hyp_table)
        log.write("\n")
    if result.errors:
        log.write(Text("Errors occurred", style="bold red"))
        for cond, err in result.errors.items():
            traceback_str = getattr(err, "traceback_str", str(err))
            log.write(Text(f"{cond}:\n{traceback_str}", style="bold yellow"))


def _has_output(result: Any) -> bool:
    if _build_experiment_table(result) is not None:
        return True
    if _build_artifact_table(result) is not None:
        return True
    if _build_hypothesis_tables(result):
        return True
    if result.errors:
        return True
    return False


def _write_summary(
    log: RichLog,
    result: Any,
    *,
    highlight: str | None = None,
    inactive: set[str] | None = None,
) -> None:
    if isinstance(result, dict):
        for name, res in result.items():
            if not _has_output(res):
                continue
            log.write(Text(name, style="bold underline"))
            _write_experiment_summary(
                log, res, highlight=highlight, inactive=inactive
            )
    else:
        _write_experiment_summary(log, result, highlight=highlight, inactive=inactive)


import json
import yaml
from pathlib import Path
from datetime import timedelta


class IndentDumper(yaml.SafeDumper):
    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


def format_seconds(seconds: float) -> str:
    """Return a human-friendly time string for ``seconds``."""
    total = int(seconds)
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours}h")
    if hours or minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def compute_static_eta(experiment_config_yaml: Path) -> timedelta:
    """Estimate total duration for an experiment from historical step timings."""
    cfg = yaml.safe_load(experiment_config_yaml.read_text()) or {}
    exp_name = cfg.get("name", experiment_config_yaml.stem)
    steps_cfg = cfg.get("steps", [])
    step_names: list[str] = []
    for st in steps_cfg:
        if isinstance(st, str):
            step_names.append(st)
        elif isinstance(st, dict):
            step_names.extend(st.keys())

    hist_file = Path.home() / ".cache" / "crystallize" / "steps" / f"{exp_name}.json"
    try:
        history = json.loads(hist_file.read_text())
    except Exception:
        history = {}

    total = 0.0
    for name in step_names:
        class_name = f"{name.title()}Step"
        durations = history.get(class_name, [])
        if durations:
            avg = sum(durations) / len(durations)
            total += avg
    return timedelta(seconds=total)


def create_experiment_scaffolding(
    name: str,
    *,
    directory: Path = Path("experiments"),
    steps: bool = True,
    datasources: bool = True,
    outputs: bool = False,
    hypotheses: bool = False,
    examples: bool = False,
    artifact_inputs: dict[str, str] | None = None,
) -> Path:
    """Create a new experiment folder with optional example code.

    Parameters
    ----------
    artifact_inputs:
        Mapping of datasource alias to ``"experiment#output"`` strings.
    """

    if not name or not name.islower() or " " in name:
        raise ValueError("name must be lowercase and contain no spaces")
    directory.mkdir(exist_ok=True)
    exp_dir = directory / name
    if exp_dir.exists():
        raise FileExistsError(exp_dir)
    exp_dir.mkdir()

    experiment_class = "Experiment"
    if artifact_inputs:
        experiment_class = "ExperimentGraph"

    default_cli_config = {
        "priority": 999,
        "group": "Graphs" if artifact_inputs else "Experiments",
        "icon": "\U0001f4ca",
        "color": None,
        "hidden": False,
    }

    config: dict[str, Any] = {
        "name": name,
        "replicates": 1,
        "cli": default_cli_config,
        "datasource": {},
        "steps": [],
    }
    if artifact_inputs:
        config["datasource"].update(artifact_inputs)
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
                "baseline": {"delta": 0},
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
        ver_code = "from crystallize import verifier\n"
        if examples:
            ver_code += "\n@verifier\ndef always_sig(baseline, treatment):\n    return {'p_value': 0.01, 'significant': True}\n"
        (exp_dir / "verifiers.py").write_text(ver_code)

    main_code = ""

    main_code += "from pathlib import Path\n"
    main_code += f"from crystallize import {experiment_class}\n"
    main_code += "\n"
    main_code += (
        f"exp = {experiment_class}.from_yaml(Path(__file__).parent / 'config.yaml')\n"
    )
    main_code += "\n"
    main_code += "if __name__ == '__main__':\n"
    main_code += "    exp.run()\n"
    (exp_dir / "main.py").write_text(main_code)

    return exp_dir


def update_replicates(config_path: Path, replicates: int) -> None:
    """Update the replicates count in ``config_path``."""

    with config_path.open() as f:
        data = yaml.safe_load(f) or {}

    data["replicates"] = replicates

    with config_path.open("w") as f:
        yaml.dump(data, f, Dumper=IndentDumper, sort_keys=False)


def add_placeholder(base: Path, kind: str, name: str) -> None:
    """Ensure a skeleton function ``name`` exists for ``kind``.

    Parameters
    ----------
    base:
        Directory containing ``steps.py`` and friends.
    kind:
        One of ``"steps"``, ``"datasource"``, ``"outputs"``, ``"verifier"``.
    name:
        Name of the function to create.
    """

    mapping = {
        "steps": (
            base / "steps.py",
            ["from crystallize import pipeline_step"],
            "@pipeline_step()\ndef {name}(data):\n    return data\n",
        ),
        "datasource": (
            base / "datasources.py",
            ["from crystallize import data_source"],
            "@data_source\ndef {name}(ctx):\n    return 1\n",
        ),
        "outputs": (
            base / "outputs.py",
            ["from pathlib import Path", "from typing import Any"],
            "def {name}(p: Path) -> Any:\n    return p.read_bytes()\n",
        ),
        "verifier": (
            base / "verifiers.py",
            ["from crystallize import verifier"],
            "@verifier\ndef {name}(baseline, treatment):\n    return {{'p_value': 0.5, 'significant': False}}\n",
        ),
    }

    file_path, imports, template = mapping[kind]

    if file_path.exists():
        text = file_path.read_text()
    else:
        text = ""

    if f"def {name}(" in text:
        return

    lines = text.splitlines()

    for imp in imports:
        if imp not in text:
            lines.insert(0, imp)
            text = "\n".join(lines)

    if lines and lines[-1].strip():
        lines.append("")

    lines.append(template.format(name=name).rstrip())

    file_path.write_text("\n".join(lines) + "\n")


def _escape(text: Any) -> str:
    """Escape text for inclusion in XML output (attributes + text)."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _result_to_xml_lines(result: Any, indent: int = 0) -> list[str]:
    """Convert a Result object into an XML string list."""
    lines: list[str] = []
    prefix = "  " * indent

    metrics = result.metrics
    lines.append(f"{prefix}<Metrics>")

    all_metrics = set(metrics.baseline.metrics.keys())
    for treatment_metrics in metrics.treatments.values():
        all_metrics.update(treatment_metrics.metrics.keys())

    for metric in sorted(all_metrics):
        lines.append(f"{prefix}  <Metric name=\"{_escape(metric)}\">")

        base_val = metrics.baseline.metrics.get(metric)
        if base_val is not None:
            lines.append(
                f"{prefix}    <Value condition=\"baseline\">{_escape(base_val)}</Value>"
            )

        for treatment_name, treatment_data in metrics.treatments.items():
            val = treatment_data.metrics.get(metric)
            if val is not None:
                lines.append(
                    f"{prefix}    <Value condition=\"{_escape(treatment_name)}\">{_escape(val)}</Value>"
                )

        lines.append(f"{prefix}  </Metric>")
    lines.append(f"{prefix}</Metrics>")

    if metrics.hypotheses:
        lines.append(f"{prefix}<Hypotheses>")
        for hypothesis in metrics.hypotheses:
            lines.append(f"{prefix}  <Hypothesis name=\"{_escape(hypothesis.name)}\">")
            if hypothesis.ranking:
                ranking = ", ".join(
                    f"{name}: {score}" for name, score in hypothesis.ranking.items()
                )
                lines.append(f"{prefix}    <Ranking>{_escape(ranking)}</Ranking>")

            for treatment_name, hypothesis_result in hypothesis.results.items():
                lines.append(
                    f"{prefix}    <Result treatment=\"{_escape(treatment_name)}\">"
                )
                for key, value in hypothesis_result.items():
                    lines.append(f"{prefix}      <{key}>{_escape(value)}</{key}>")
                lines.append(f"{prefix}    </Result>")
            lines.append(f"{prefix}  </Hypothesis>")
        lines.append(f"{prefix}</Hypotheses>")

    artifacts = getattr(result, "artifacts", {})
    if artifacts:
        lines.append(f"{prefix}<Artifacts>")
        for name, mapping in artifacts.items():
            lines.append(f"{prefix}  <Artifact name=\"{_escape(name)}\">")
            for condition, path in mapping.items():
                lines.append(
                    f"{prefix}    <Path condition=\"{_escape(condition)}\">{_escape(path)}</Path>"
                )
            lines.append(f"{prefix}  </Artifact>")
        lines.append(f"{prefix}</Artifacts>")

    return lines


def generate_xml_summary(result: Any) -> str:
    """Generate an XML summary suitable for LLM consumption."""
    lines = ["<CrystallizeSummary>"]
    if isinstance(result, dict):
        for name, res in result.items():
            lines.append(f"  <Experiment name=\"{_escape(name)}\">")
            lines.extend(_result_to_xml_lines(res, indent=2))
            lines.append("  </Experiment>")
    else:
        lines.extend(_result_to_xml_lines(result, indent=1))
    lines.append("</CrystallizeSummary>")
    return "\n".join(lines)
