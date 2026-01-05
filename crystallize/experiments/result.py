from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .result_structs import ExperimentMetrics, HypothesisResult


class Result:
    """Outputs of an experiment run including metrics and provenance."""

    def __init__(
        self,
        metrics: ExperimentMetrics,
        artifacts: Optional[Dict[str, Any]] = None,
        errors: Optional[Dict[str, Exception]] = None,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.metrics = metrics
        self.artifacts = artifacts or {}
        self.errors = errors or {}
        self.provenance = provenance or {}

    def get_artifact(self, name: str) -> Any:
        """Return an artifact by name if it was recorded."""
        return self.artifacts.get(name)

    # Convenience
    def get_hypothesis(self, name: str) -> Optional[HypothesisResult]:
        """Return the :class:`HypothesisResult` with ``name`` if present."""
        return next(
            (h for h in self.metrics.hypotheses if h.name == name),
            None,
        )

    # ------------------------------------------------------------------ #
    def print_tree(self, fmt: str = "treatment > replicate > step") -> None:
        """Print a color-coded tree of execution provenance.

        The ``fmt`` string controls the hierarchy of the output.  Valid tokens
        are ``"treatment"``, ``"replicate"``, ``"step"`` and ``"action"``.  When
        ``"action"`` is included as the final element, each step lists the
        values read, metrics written and context mutations that occurred.

        The function uses :mod:`rich` to render a pretty tree if the package is
        installed; otherwise a plain-text version is printed.

        Parameters
        ----------
        fmt:
            Format specification controlling how provenance records are grouped.
            The default groups by treatment, replicate and step.

        Raises
        ------
        ValueError
            If the format specification contains unknown tokens or ``"action"``
            is not the final element.
        """
        tokens = [t.strip().lower() for t in fmt.split(">")]
        valid = {"treatment", "replicate", "step", "action"}
        if any(tok not in valid for tok in tokens):
            raise ValueError(f"Invalid format spec: {fmt}")
        if "action" in tokens and tokens[-1] != "action":
            raise ValueError("'action' must be the final element if present")

        changes = self.provenance.get("ctx_changes", {})
        rows = []
        for treatment, reps in changes.items():
            for rep, steps in reps.items():
                for record in steps:
                    acts = record.get("ctx_changes", {})
                    if not any(acts.get(a) for a in ("reads", "wrote", "metrics")):
                        continue
                    rows.append(
                        {
                            "treatment": treatment,
                            "replicate": rep,
                            "step": record.get("step", ""),
                            "actions": acts,
                        }
                    )

        try:
            from rich.console import Console
            from rich.tree import Tree

            use_rich = True
        except Exception:  # pragma: no cover - optional dependency
            use_rich = False

        class Node:
            def __init__(self, label: str, style: Optional[str] = None) -> None:
                self.label = label
                self.style = style
                self.children: list["Node"] = []

            def add(self, label: str, style: Optional[str] = None) -> "Node":
                child = Node(label, style)
                self.children.append(child)
                return child

        root = Node("Experiment Summary", "bold")

        color_order = ["bold yellow", "green", "cyan"]

        def get_color(token: str) -> str:
            return color_order[tokens.index(token)]

        level_styles: Dict[str, str] = {
            "treatment": get_color("treatment"),
            "replicate": get_color("replicate"),
            "step": get_color("step"),
        }

        def add_actions(parent: Node, acts: Dict[str, Any]) -> None:
            mapping = {
                "reads": ("Reads", "green"),
                "wrote": ("Writes", "blue"),
                "metrics": ("Write Metrics", "red"),
            }
            for key, (label, style) in mapping.items():
                details = acts.get(key, {})
                if not details:
                    continue
                act_node = parent.add(label, style)
                if key == "reads":
                    for k, v in details.items():
                        act_node.add(f"{k}={v}")
                else:
                    for k, change in details.items():
                        before = change.get("before")
                        after = change.get("after")
                        act_node.add(f"{k}: {before} -> {after}")

        def build(node: Node, subset: list[dict], level: int) -> None:
            if level == len(tokens):
                for row in subset:
                    step_node = node
                    if "step" not in tokens:
                        step_node = node.add(
                            f"Step {row['step']}", level_styles.get("step")
                        )
                    add_actions(step_node, row["actions"])
                return

            token = tokens[level]
            if token == "action":
                for row in subset:
                    step_node = node
                    if "step" not in tokens[:level]:
                        step_node = node.add(
                            f"Step {row['step']}", level_styles.get("step")
                        )
                    add_actions(step_node, row["actions"])
                return

            groups: Dict[Any, list[dict]] = {}
            for row in subset:
                groups.setdefault(row[token], []).append(row)

            for key in sorted(groups):
                if token == "treatment":
                    label = f"Treatment '{key}'"
                elif token == "replicate":
                    label = f"Replicate {key}"
                else:  # step
                    label = f"Step {key}"
                style = level_styles.get(token)
                child = node.add(label, style)
                build(child, groups[key], level + 1)

        build(root, rows, 0)

        if use_rich:
            console = Console()

            def to_rich(rnode: Node) -> Tree:
                label = (
                    f"[{rnode.style}]" + rnode.label + "[/]"
                    if rnode.style
                    else rnode.label
                )
                r_tree = Tree(label)
                for c in rnode.children:
                    r_tree.add(to_rich(c))
                return r_tree

            console.print(to_rich(root))
        else:  # pragma: no cover - fallback

            def print_plain(pnode: Node, depth: int = 0) -> None:
                indent = "  " * depth
                print(f"{indent}{pnode.label}")
                for c in pnode.children:
                    print_plain(c, depth + 1)

            print_plain(root)

    # ------------------------------------------------------------------ #
    # Persistence methods
    # ------------------------------------------------------------------ #
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to a serializable dictionary.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing metrics, hypotheses, artifacts metadata,
            errors, and provenance. Safe for JSON serialization.
        """

        def _serialize_metrics(tm: Any) -> Dict[str, List[Any]]:
            return {k: list(v) for k, v in tm.metrics.items()}

        hypotheses_data = [
            {"name": h.name, "results": h.results, "ranking": h.ranking}
            for h in self.metrics.hypotheses
        ]

        # Serialize errors as strings (exceptions aren't JSON-safe)
        errors_data = {k: str(v) for k, v in self.errors.items()}

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "baseline": _serialize_metrics(self.metrics.baseline),
                "treatments": {
                    name: _serialize_metrics(tm)
                    for name, tm in self.metrics.treatments.items()
                },
            },
            "hypotheses": hypotheses_data,
            "artifacts": list(self.artifacts.keys()),  # Just names, not binary data
            "errors": errors_data,
            "provenance": self.provenance,
        }

    def to_json(
        self, path: Optional[Union[str, Path]] = None, indent: int = 2
    ) -> Optional[str]:
        """Serialize results to JSON.

        Parameters
        ----------
        path:
            If provided, write JSON to this file path. If None, return as string.
        indent:
            JSON indentation level. Default is 2.

        Returns
        -------
        Optional[str]
            JSON string if no path provided, otherwise None (writes to file).

        Example
        -------
        >>> result.to_json("experiment_results.json")
        >>> # or get as string
        >>> json_str = result.to_json()
        """
        data = self.to_dict()
        if path is not None:
            Path(path).write_text(json.dumps(data, indent=indent, default=str))
            return None
        return json.dumps(data, indent=indent, default=str)

    def to_parquet(self, path: Union[str, Path]) -> None:
        """Save metrics as a Parquet file for efficient analysis.

        Creates a flat table with columns: condition, metric, values, hypothesis_*

        Parameters
        ----------
        path:
            File path for the Parquet output.

        Raises
        ------
        ImportError
            If pandas or pyarrow is not installed.

        Example
        -------
        >>> result.to_parquet("experiment_results.parquet")
        >>> # Load later with pandas
        >>> import pandas as pd
        >>> df = pd.read_parquet("experiment_results.parquet")
        """
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError(
                "pandas is required for to_parquet(). Install with: pip install pandas"
            ) from e

        rows: List[Dict[str, Any]] = []

        # Add baseline metrics
        for metric, values in self.metrics.baseline.metrics.items():
            rows.append(
                {
                    "condition": "baseline",
                    "metric": metric,
                    "values": values,
                    "mean": sum(values) / len(values) if values else None,
                }
            )

        # Add treatment metrics
        for treatment, tm in self.metrics.treatments.items():
            for metric, values in tm.metrics.items():
                rows.append(
                    {
                        "condition": treatment,
                        "metric": metric,
                        "values": values,
                        "mean": sum(values) / len(values) if values else None,
                    }
                )

        df = pd.DataFrame(rows)
        df.to_parquet(path, index=False)
