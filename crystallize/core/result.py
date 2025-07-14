from __future__ import annotations

from typing import Any, Dict, Optional

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
        """Print a tree summary of execution provenance."""
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

        color_order = ['bold yellow', 'green', 'cyan']

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
