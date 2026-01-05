"""Crystallize: From Play to Proof.

Run experiments. Start exploring, then crystallize with a hypothesis.
"""

from __future__ import annotations

import inspect
import random
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn


@dataclass
class Context:
    """Execution context for recording metrics during a run.

    Example
    -------
    >>> def my_fn(config, ctx):
    ...     result = do_something(config)
    ...     ctx.record("accuracy", result.accuracy)
    ...     ctx.record("latency", result.latency, tags={"unit": "ms"})
    ...     return result
    """

    replicate: int
    config_name: str
    seed: Optional[int] = None
    _metrics: Dict[str, List[Any]] = field(default_factory=dict)
    _tags: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)

    def record(self, name: str, value: Any, tags: Optional[Dict[str, Any]] = None) -> None:
        """Record a metric value.

        Parameters
        ----------
        name : str
            Metric name (e.g., "accuracy", "win_rate", "latency")
        value : Any
            The value to record
        tags : dict, optional
            Additional metadata for this measurement
        """
        if name not in self._metrics:
            self._metrics[name] = []
            self._tags[name] = []
        self._metrics[name].append(value)
        self._tags[name].append(tags or {})

    @property
    def metrics(self) -> Dict[str, List[Any]]:
        """Access recorded metrics."""
        return self._metrics.copy()


@dataclass
class HypothesisResult:
    """Statistical test results."""
    hypothesis: str
    supported: bool
    left_config: str
    right_config: str
    metric: str
    operator: str
    left_mean: float
    right_mean: float
    effect_size: float
    p_value: float
    n_left: int
    n_right: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hypothesis": self.hypothesis,
            "supported": self.supported,
            "left_config": self.left_config,
            "right_config": self.right_config,
            "metric": self.metric,
            "operator": self.operator,
            "left_mean": self.left_mean,
            "right_mean": self.right_mean,
            "effect_size": self.effect_size,
            "p_value": self.p_value,
            "n_left": self.n_left,
            "n_right": self.n_right,
        }


@dataclass
class RunResult:
    """Results from crystallize.run().

    Attributes
    ----------
    results : dict
        Raw return values: {config_name: [result_per_replicate]}
    metrics : dict
        Recorded metrics: {config_name: {metric_name: [values]}}
    hypothesis_result : HypothesisResult, optional
        Statistical test results if hypothesis was provided
    """
    results: Dict[str, List[Any]]
    metrics: Dict[str, Dict[str, List[Any]]]
    hypothesis_result: Optional[HypothesisResult] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "results": self.results,
            "metrics": self.metrics,
            "hypothesis_result": self.hypothesis_result.to_dict() if self.hypothesis_result else None,
        }

    def to_json(self, path: Optional[str] = None, indent: int = 2) -> Optional[str]:
        """Serialize to JSON. Writes to file if path provided, else returns string."""
        import json
        from datetime import datetime

        data = {"timestamp": datetime.now().isoformat(), **self.to_dict()}
        json_str = json.dumps(data, indent=indent, default=str)

        if path:
            with open(path, "w") as f:
                f.write(json_str)
            return None
        return json_str


@dataclass
class _ParsedHypothesis:
    """Internal: parsed hypothesis string."""
    left_config: str
    left_metric: str
    operator: str
    right_config: str
    right_metric: str


def _parse_hypothesis(hypothesis: str) -> _ParsedHypothesis:
    """Parse 'config.metric > config.metric' format."""
    pattern = r"(\w+)\.(\w+)\s*(>=|<=|>|<)\s*(\w+)\.(\w+)"
    match = re.match(pattern, hypothesis.strip())

    if not match:
        raise ValueError(
            f"Invalid hypothesis: '{hypothesis}'\n"
            f"Expected format: 'config.metric > config.metric'\n"
            f"Example: 'treatment.accuracy > baseline.accuracy'"
        )

    left_config, left_metric, operator, right_config, right_metric = match.groups()
    return _ParsedHypothesis(
        left_config=left_config,
        left_metric=left_metric,
        operator=operator,
        right_config=right_config,
        right_metric=right_metric,
    )


def _run_test(
    left: List[float],
    right: List[float],
    operator: str
) -> Tuple[float, float, bool]:
    """Run statistical test. Returns (effect_size, p_value, supported)."""

    left_mean = sum(left) / len(left) if left else 0
    right_mean = sum(right) / len(right) if right else 0
    effect_size = left_mean - right_mean

    # Try scipy for proper statistics
    try:
        from scipy import stats

        is_binary = set(left + right).issubset({0, 1, 0.0, 1.0})

        if is_binary:
            # Fisher's exact for binary outcomes
            table = [
                [int(sum(left)), len(left) - int(sum(left))],
                [int(sum(right)), len(right) - int(sum(right))]
            ]
            alt = "greater" if operator in (">", ">=") else "less" if operator in ("<", "<=") else "two-sided"
            _, p_value = stats.fisher_exact(table, alternative=alt)
        else:
            # T-test for continuous
            alt = "greater" if operator in (">", ">=") else "less" if operator in ("<", "<=") else "two-sided"
            _, p_value = stats.ttest_ind(left, right, alternative=alt)

        p_value = float(p_value)

    except ImportError:
        # No scipy - just compare means, p=nan
        p_value = float("nan")

    # Determine support
    if operator == ">":
        supported = left_mean > right_mean and (p_value < 0.05 or p_value != p_value)
    elif operator == "<":
        supported = left_mean < right_mean and (p_value < 0.05 or p_value != p_value)
    elif operator == ">=":
        supported = left_mean >= right_mean and (p_value < 0.05 or p_value != p_value)
    elif operator == "<=":
        supported = left_mean <= right_mean and (p_value < 0.05 or p_value != p_value)
    else:
        supported = False

    return effect_size, p_value, supported


def run(
    fn: Callable[..., Any],
    configs: Optional[Dict[str, Any]] = None,
    replicates: int = 1,
    *,
    seed: Optional[int] = None,
    hypothesis: Optional[str] = None,
    on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    progress: bool = True,
) -> RunResult:
    """Run an experiment. Start exploring, then crystallize with a hypothesis.

    Parameters
    ----------
    fn : Callable
        Your function. Signature options:
        - fn(config) - receives config dict
        - fn(config, ctx) - receives config and context for recording metrics

    configs : dict
        Configurations to compare. Keys are names, values are config dicts.
        Example: {"baseline": {"model": "A"}, "treatment": {"model": "B"}}

    replicates : int
        Times to run each config. Default 1.

    seed : int, optional
        Random seed for reproducibility.

    hypothesis : str, optional
        Claim to test. Triggers confirmatory mode.
        Format: "config.metric > config.metric"
        Example: "treatment.win_rate > baseline.win_rate"

    on_event : Callable, optional
        Callback for live updates. Receives event dicts with keys:
        type, config, replicate, metric, value, result

    progress : bool
        Show progress bar. Default True.

    Returns
    -------
    RunResult
        Contains results, metrics, and hypothesis_result (if hypothesis provided).

    Examples
    --------
    Exploratory (no hypothesis):

    >>> results = run(
    ...     fn=play_game,
    ...     configs={"a": {"x": 1}, "b": {"x": 2}},
    ...     replicates=5,
    ... )

    Confirmatory (with hypothesis):

    >>> results = run(
    ...     fn=play_game,
    ...     configs={"baseline": {...}, "treatment": {...}},
    ...     replicates=20,
    ...     hypothesis="treatment.win_rate > baseline.win_rate",
    ...     seed=42,
    ... )
    """
    console = Console()

    # Parse hypothesis
    parsed: Optional[_ParsedHypothesis] = None
    if hypothesis:
        parsed = _parse_hypothesis(hypothesis)

    # Default config
    if configs is None:
        configs = {"baseline": {}}

    # Validate hypothesis references existing configs
    if parsed:
        for name in [parsed.left_config, parsed.right_config]:
            if name not in configs:
                raise ValueError(
                    f"Hypothesis references '{name}' but configs only has: {list(configs.keys())}"
                )

    # Detect function signature
    sig = inspect.signature(fn)
    params = list(sig.parameters.keys())
    wants_ctx = "ctx" in params or len(params) >= 2

    # Print header
    if hypothesis:
        console.print("\n[bold green]✓[/] [bold]Confirmatory mode[/]")
        console.print(f"  Hypothesis: [cyan]{hypothesis}[/]")
        if seed is not None:
            console.print(f"  Seed: {seed}")
        console.print()
    else:
        console.print("\n[yellow]⚠[/]  [bold]Exploratory mode[/] — perfect for playing around.")
        console.print("    When ready to prove something: [cyan]hypothesis=\"a.x > b.x\"[/]\n")

    # Emit start
    if on_event:
        on_event({"type": "start", "configs": list(configs.keys()), "replicates": replicates})

    # Storage
    results: Dict[str, List[Any]] = {name: [] for name in configs}
    metrics: Dict[str, Dict[str, List[Any]]] = {name: {} for name in configs}

    total = len(configs) * replicates

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        disable=not progress,
    ) as pbar:
        task = pbar.add_task("Running...", total=total)

        for config_name, config in configs.items():
            for i in range(replicates):
                pbar.update(task, description=f"[cyan]{config_name}[/] [{i+1}/{replicates}]")

                # Seed
                if seed is not None:
                    rep_seed = seed + i * 31337
                    random.seed(rep_seed)
                    try:
                        import numpy as np
                        np.random.seed(rep_seed)
                    except ImportError:
                        pass

                # Context
                ctx = Context(replicate=i, config_name=config_name, seed=seed)

                # Event: start
                if on_event:
                    on_event({"type": "replicate_start", "config": config_name, "replicate": i})

                # Run
                if wants_ctx:
                    result = fn(config, ctx)
                else:
                    result = fn(config)

                results[config_name].append(result)

                # Collect metrics
                for metric_name, values in ctx.metrics.items():
                    if metric_name not in metrics[config_name]:
                        metrics[config_name][metric_name] = []
                    # Take last value if multiple recorded per replicate
                    if values:
                        metrics[config_name][metric_name].append(values[-1])
                        if on_event:
                            on_event({
                                "type": "metric",
                                "config": config_name,
                                "replicate": i,
                                "metric": metric_name,
                                "value": values[-1],
                            })

                # Event: end
                if on_event:
                    on_event({"type": "replicate_end", "config": config_name, "replicate": i, "result": result})

                pbar.advance(task)

    # Statistical test
    hyp_result: Optional[HypothesisResult] = None

    if parsed:
        left_vals = metrics.get(parsed.left_config, {}).get(parsed.left_metric, [])
        right_vals = metrics.get(parsed.right_config, {}).get(parsed.right_metric, [])

        if not left_vals:
            console.print(f"\n[red]✗ No '{parsed.left_metric}' recorded for '{parsed.left_config}'[/]")
        elif not right_vals:
            console.print(f"\n[red]✗ No '{parsed.right_metric}' recorded for '{parsed.right_config}'[/]")
        else:
            effect, pval, supported = _run_test(left_vals, right_vals, parsed.operator)
            left_mean = sum(left_vals) / len(left_vals)
            right_mean = sum(right_vals) / len(right_vals)

            hyp_result = HypothesisResult(
                hypothesis=hypothesis,
                supported=supported,
                left_config=parsed.left_config,
                right_config=parsed.right_config,
                metric=parsed.left_metric,
                operator=parsed.operator,
                left_mean=left_mean,
                right_mean=right_mean,
                effect_size=effect,
                p_value=pval,
                n_left=len(left_vals),
                n_right=len(right_vals),
            )

            console.print()
            if supported:
                console.print("[bold green]✓ Hypothesis SUPPORTED[/]")
            else:
                console.print("[bold red]✗ Hypothesis NOT SUPPORTED[/]")

            console.print(
                f"  {parsed.left_config}.{parsed.left_metric} (μ={left_mean:.2f}, n={len(left_vals)}) "
                f"{parsed.operator} "
                f"{parsed.right_config}.{parsed.right_metric} (μ={right_mean:.2f}, n={len(right_vals)})"
            )
            console.print(f"  Effect size: {effect:.2f}, p={pval:.3f}")
            console.print()
    else:
        # Exploratory summary
        console.print("[bold]Results:[/]")
        for config_name, config_metrics in metrics.items():
            if config_metrics:
                console.print(f"  [cyan]{config_name}[/]:")
                for metric_name, values in config_metrics.items():
                    mean = sum(values) / len(values) if values else 0
                    console.print(f"    {metric_name}: {values} → μ={mean:.2f}")
        console.print()

    # Event: end
    if on_event:
        on_event({"type": "end", "results": results, "metrics": metrics})

    return RunResult(results=results, metrics=metrics, hypothesis_result=hyp_result)
