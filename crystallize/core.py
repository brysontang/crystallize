"""Core Crystallize API: explore() and crystallize().

This module provides the main API for running experiments.
"""

from __future__ import annotations

import inspect
import random
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn

from .context import create_context
from .fingerprint import fn_fingerprint, fingerprints_match
from .ids import config_fingerprint, generate_lineage_id, generate_run_id, manifest_hash
from .integrity import (
    IntegrityStatus,
    check_blocking_conditions,
    compute_integrity,
    format_integrity_header,
)
from .protocol import HiddenVariablesReport, ProtocolDiff, ProtocolSummary
from .stats import check_hypothesis
from .store import Store, get_store


# Hypothesis parsing
@dataclass
class ParsedHypothesis:
    """Parsed hypothesis string."""

    left_config: str
    left_metric: str
    operator: str
    right_config: str
    right_metric: str
    raw: str


def parse_hypothesis(hypothesis: str) -> ParsedHypothesis:
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
    return ParsedHypothesis(
        left_config=left_config,
        left_metric=left_metric,
        operator=operator,
        right_config=right_config,
        right_metric=right_metric,
        raw=hypothesis,
    )


def _get_git_info() -> Dict[str, Any]:
    """Get git commit and dirty status."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if commit.returncode == 0:
            return {
                "commit": commit.stdout.strip()[:12],
                "dirty": bool(status.stdout.strip()) if status.returncode == 0 else None,
            }
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return {"commit": None, "dirty": None}


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
    ci: Tuple[float, float]
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
            "ci": list(self.ci),
            "n_left": self.n_left,
            "n_right": self.n_right,
        }


@dataclass
class ConfirmRun:
    """Results from exp.crystallize().

    Attributes
    ----------
    run_id : str
        Unique ID for this confirm run
    parent_run_id : str
        ID of the explore run this extends
    lineage_id : str
        Lineage ID shared with parent
    hypothesis : str
        The tested hypothesis
    supported : bool, optional
        Whether hypothesis was supported
    hypothesis_result : HypothesisResult, optional
        Full statistical results
    integrity : IntegrityStatus
        Integrity status
    integrity_flags : list
        List of integrity flag codes
    prereg_path : str
        Path to pre-registration artifact
    results_path : str
        Path to results manifest
    git : dict
        Git commit and dirty status
    fn_fingerprint : dict
        Function fingerprint
    results : dict
        Raw return values
    metrics : dict
        Recorded metrics
    """

    run_id: str
    parent_run_id: str
    lineage_id: str
    hypothesis: str
    supported: Optional[bool] = None
    hypothesis_result: Optional[HypothesisResult] = None
    integrity: IntegrityStatus = IntegrityStatus.INVALID
    integrity_flags: List[str] = field(default_factory=list)
    prereg_path: Optional[str] = None
    results_path: Optional[str] = None
    git: Dict[str, Any] = field(default_factory=dict)
    fn_fingerprint: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, List[Any]] = field(default_factory=dict)
    metrics: Dict[str, Dict[str, List[Any]]] = field(default_factory=dict)
    replicate_range: Tuple[int, int] = (0, 0)

    def report(self) -> str:
        """Generate a formatted report of the confirm run."""
        lines = []

        # Integrity header (always first)
        lines.append(format_integrity_header(self.integrity, self.integrity_flags))
        lines.append("")

        # Hypothesis result
        if self.hypothesis_result:
            hr = self.hypothesis_result
            if hr.supported:
                lines.append(f"✓ Hypothesis SUPPORTED: {self.hypothesis}")
            else:
                lines.append(f"✗ Hypothesis NOT SUPPORTED: {self.hypothesis}")

            lines.append(
                f"  {hr.left_config}.{hr.metric} (μ={hr.left_mean:.3f}, n={hr.n_left}) "
                f"{hr.operator} "
                f"{hr.right_config}.{hr.metric} (μ={hr.right_mean:.3f}, n={hr.n_right})"
            )
            lines.append(f"  Effect: {hr.effect_size:.3f}, 95% CI [{hr.ci[0]:.3f}, {hr.ci[1]:.3f}]")
            lines.append(f"  p = {hr.p_value:.4f}")
            lines.append("")

        # Proof block
        lines.append("Proof:")
        lines.append(f"  run_id: {self.run_id}")
        lines.append(f"  parent: {self.parent_run_id}")
        lines.append(f"  lineage: {self.lineage_id}")
        if self.prereg_path:
            lines.append(f"  prereg: {self.prereg_path}")
        lines.append(f"  replicates: {self.replicate_range[0]}-{self.replicate_range[1]}")
        if self.fn_fingerprint:
            lines.append(f"  fn_sha: {self.fn_fingerprint.get('sha256', 'N/A')[:12]}")
        if self.git.get("commit"):
            dirty = " (dirty)" if self.git.get("dirty") else ""
            lines.append(f"  git: {self.git['commit']}{dirty}")
        if self.results_path:
            lines.append(f"  results: {self.results_path}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "parent_run_id": self.parent_run_id,
            "lineage_id": self.lineage_id,
            "hypothesis": self.hypothesis,
            "supported": self.supported,
            "hypothesis_result": self.hypothesis_result.to_dict() if self.hypothesis_result else None,
            "integrity": self.integrity.value,
            "integrity_flags": self.integrity_flags,
            "prereg_path": self.prereg_path,
            "results_path": self.results_path,
            "git": self.git,
            "fn_fingerprint": self.fn_fingerprint,
            "results": self.results,
            "metrics": self.metrics,
            "replicate_range": list(self.replicate_range),
        }


@dataclass
class Experiment:
    """Results from explore().

    Attributes
    ----------
    run_id : str
        Unique ID for this explore run
    lineage_id : str
        Lineage ID (for tracking related runs)
    seed : int, optional
        Random seed used
    configs : dict
        The config dictionaries
    config_fingerprints : dict
        Fingerprints for each config
    results : dict
        Raw return values: {config_name: [result_per_replicate]}
    metrics : dict
        Recorded metrics: {config_name: {metric_name: [values]}}
    protocol : dict
        Protocol summaries: {config_name: ProtocolSummary}
    audit_level : str
        Audit level used
    fn_fingerprint : dict
        Function fingerprint
    paths : dict
        Paths to stored artifacts
    """

    run_id: str
    lineage_id: str
    seed: Optional[int]
    configs: Dict[str, Dict[str, Any]]
    config_fingerprints: Dict[str, str]
    results: Dict[str, List[Any]]
    metrics: Dict[str, Dict[str, List[Any]]]
    protocol: Dict[str, ProtocolSummary]
    audit_level: str
    fn_fingerprint: Dict[str, Any]
    fn: Callable[..., Any]  # Keep reference for crystallize
    paths: Dict[str, str] = field(default_factory=dict)
    _store: Optional[Store] = field(default=None, repr=False)

    def protocol_report(self) -> str:
        """Generate a formatted protocol report."""
        lines = ["Protocol Report", "=" * 40]

        for config_name, summary in self.protocol.items():
            lines.append(f"\n{config_name}:")
            lines.append(f"  Instrumented calls: {summary.audit_evidence.get('instrumented_call_count', 0)}")

            for call in summary.api_calls:
                lines.append(f"  - {call['method']} {call['host']}{call['path']}")
                for field_name, field_info in call.get("fields", {}).items():
                    lines.append(f"      {field_name}: {field_info.get('value')!r} ({field_info.get('source')})")

        return "\n".join(lines)

    def protocol_diff(self) -> ProtocolDiff:
        """Get protocol diff between configs."""
        return ProtocolDiff.from_configs_and_summaries(self.configs, self.protocol)

    def hidden_variables(self) -> HiddenVariablesReport:
        """Get hidden variables report."""
        return HiddenVariablesReport.from_protocol_summaries(self.protocol)

    def crystallize(
        self,
        hypothesis: str,
        replicates: int = 20,
        *,
        allow_reuse: bool = False,
        allow_confounds: bool = False,
        allow_no_audit: bool = False,
        allow_fn_change: bool = False,
        reason: Optional[str] = None,
        progress: bool = True,
        seed: Optional[int] = None,
    ) -> ConfirmRun:
        """Crystallize: run confirmatory replicates with a hypothesis.

        Parameters
        ----------
        hypothesis : str
            Hypothesis to test (e.g., "treatment.accuracy > baseline.accuracy")
        replicates : int
            Number of replicates per config
        allow_reuse : bool
            Allow reusing data (results in REUSED_DATA status)
        allow_confounds : bool
            Allow confounds (results in CONFOUNDED status)
        allow_no_audit : bool
            Allow no audit (results in NO_AUDIT status)
        allow_fn_change : bool
            Allow function change (results in FN_CHANGED status)
        reason : str, optional
            Reason for any overrides
        progress : bool
            Show progress bar
        seed : int, optional
            Random seed for confirm run (defaults to explore seed)

        Returns
        -------
        ConfirmRun
            Results with integrity status
        """
        console = Console()

        # Parse hypothesis
        parsed = parse_hypothesis(hypothesis)

        # Validate configs referenced in hypothesis exist
        for name in [parsed.left_config, parsed.right_config]:
            if name not in self.configs:
                raise ValueError(
                    f"Hypothesis references '{name}' but configs only has: {list(self.configs.keys())}"
                )

        # Get current function fingerprint
        current_fp = fn_fingerprint(self.fn)
        fn_match = fingerprints_match(self.fn_fingerprint, current_fp)

        # Check hidden variables
        hidden_vars = self.hidden_variables()

        # Check blocking conditions
        blocking = check_blocking_conditions(
            hidden_vars=hidden_vars,
            audit_level=self.audit_level,
            fn_fingerprint_match=fn_match,
            allow_confounds=allow_confounds,
            allow_no_audit=allow_no_audit,
            allow_fn_change=allow_fn_change,
        )

        if blocking:
            raise RuntimeError(f"Cannot crystallize:\n\n{blocking}")

        # Get store
        store = self._store or get_store()

        # Generate confirm run ID
        run_id = generate_run_id("confirm")

        # Allocate fresh replicate indices
        replicate_ranges: Dict[str, Tuple[int, int]] = {}
        for config_name, cfg_fp in self.config_fingerprints.items():
            start, end = store.allocate_replicates(self.lineage_id, cfg_fp, replicates)
            replicate_ranges[config_name] = (start, end)

        # Write pre-registration (BEFORE running)
        prereg_data = {
            "run_id": run_id,
            "parent_run_id": self.run_id,
            "lineage_id": self.lineage_id,
            "hypothesis": hypothesis,
            "replicates_per_config": replicates,
            "config_fingerprints": self.config_fingerprints,
            "replicate_ranges": {k: list(v) for k, v in replicate_ranges.items()},
            "fn_fingerprint": current_fp,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "overrides": {
                "allow_reuse": allow_reuse,
                "allow_confounds": allow_confounds,
                "allow_no_audit": allow_no_audit,
                "allow_fn_change": allow_fn_change,
            },
            "reason": reason,
        }
        prereg_path = store.write_prereg(run_id, prereg_data)

        # Print header
        console.print(f"\n[bold green]✓[/] [bold]Confirmatory mode[/] (run: {run_id})")
        console.print(f"  Hypothesis: [cyan]{hypothesis}[/]")
        console.print(f"  Parent: {self.run_id}")

        confirm_seed = seed if seed is not None else self.seed

        if confirm_seed is not None:
            console.print(f"  Seed: {confirm_seed}")
        console.print()

        # Detect function signature
        sig = inspect.signature(self.fn)
        params = list(sig.parameters.keys())
        wants_ctx = "ctx" in params or len(params) >= 2

        # Run confirm replicates
        confirm_results: Dict[str, List[Any]] = {name: [] for name in self.configs}
        confirm_metrics: Dict[str, Dict[str, List[Any]]] = {name: {} for name in self.configs}
        protocol_events: Dict[str, List[Any]] = {name: [] for name in self.configs}

        total = len(self.configs) * replicates

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            disable=not progress,
        ) as pbar:
            task = pbar.add_task("Confirming...", total=total)

            for config_name, config in self.configs.items():
                cfg_fp = self.config_fingerprints[config_name]
                start_idx, _ = replicate_ranges[config_name]

                for i in range(replicates):
                    global_idx = start_idx + i
                    pbar.update(task, description=f"[cyan]{config_name}[/] [{i+1}/{replicates}]")

                    # Seed
                    if confirm_seed is not None:
                        rep_seed = confirm_seed + global_idx * 31337
                        random.seed(rep_seed)
                        try:
                            import numpy as np
                            np.random.seed(rep_seed)
                        except ImportError:
                            pass

                    # Create context
                    ctx = create_context(
                        replicate=i,
                        config_name=config_name,
                        config_fingerprint=cfg_fp,
                        config=config,
                        seed=confirm_seed,
                        replicate_id=f"rep_{self.lineage_id}_{cfg_fp[:8]}_{global_idx:04d}",
                        audit=self.audit_level,
                    )

                    # Run function
                    if wants_ctx:
                        result = self.fn(config, ctx)
                    else:
                        result = self.fn(config)

                    confirm_results[config_name].append(result)

                    # Collect metrics
                    for metric_name, values in ctx.metrics.items():
                        if metric_name not in confirm_metrics[config_name]:
                            confirm_metrics[config_name][metric_name] = []
                        if values:
                            confirm_metrics[config_name][metric_name].append(values[-1])

                    # Collect protocol events
                    protocol_events[config_name].extend(ctx._get_protocol_events())

                    pbar.advance(task)

        # Run statistical test
        left_vals = confirm_metrics.get(parsed.left_config, {}).get(parsed.left_metric, [])
        right_vals = confirm_metrics.get(parsed.right_config, {}).get(parsed.right_metric, [])

        hyp_result: Optional[HypothesisResult] = None
        supported: Optional[bool] = None

        if left_vals and right_vals:
            is_supported, eff, p_val, ci = check_hypothesis(
                left_vals, right_vals, parsed.operator, seed=confirm_seed
            )

            left_mean = sum(left_vals) / len(left_vals)
            right_mean = sum(right_vals) / len(right_vals)

            hyp_result = HypothesisResult(
                hypothesis=hypothesis,
                supported=is_supported,
                left_config=parsed.left_config,
                right_config=parsed.right_config,
                metric=parsed.left_metric,
                operator=parsed.operator,
                left_mean=left_mean,
                right_mean=right_mean,
                effect_size=eff,
                p_value=p_val,
                ci=ci,
                n_left=len(left_vals),
                n_right=len(right_vals),
            )
            supported = is_supported

        # Compute integrity status
        overrides = []
        if allow_reuse:
            overrides.append("allow_reuse")
        if allow_confounds:
            overrides.append("allow_confounds")
        if allow_no_audit:
            overrides.append("allow_no_audit")
        if allow_fn_change:
            overrides.append("allow_fn_change")

        # Check fresh replicates (we just allocated them, so they're fresh unless allow_reuse)
        replicates_fresh = not allow_reuse

        integrity_status, integrity_flags = compute_integrity(
            prereg_exists=True,
            replicates_fresh=replicates_fresh,
            hidden_vars=hidden_vars,
            audit_sufficient=self.audit_level == "calls",
            fn_changed=not fn_match,
            overrides=overrides,
            sample_size=len(left_vals) + len(right_vals),
        )

        # Get git info
        git_info = _get_git_info()

        # Calculate overall replicate range
        all_starts = [r[0] for r in replicate_ranges.values()]
        all_ends = [r[1] for r in replicate_ranges.values()]
        overall_range = (min(all_starts), max(all_ends))

        # Build confirm run
        confirm_run = ConfirmRun(
            run_id=run_id,
            parent_run_id=self.run_id,
            lineage_id=self.lineage_id,
            hypothesis=hypothesis,
            supported=supported,
            hypothesis_result=hyp_result,
            integrity=integrity_status,
            integrity_flags=integrity_flags,
            prereg_path=str(prereg_path),
            git=git_info,
            fn_fingerprint=current_fp,
            results=confirm_results,
            metrics=confirm_metrics,
            replicate_range=overall_range,
        )

        # Write results manifest
        manifest = confirm_run.to_dict()
        manifest["manifest_hash"] = manifest_hash(manifest)
        results_path = store.write_run_manifest(run_id, manifest)
        confirm_run.results_path = str(results_path)

        # Print results
        console.print()
        console.print(confirm_run.report())

        return confirm_run

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "run_id": self.run_id,
            "lineage_id": self.lineage_id,
            "seed": self.seed,
            "configs": self.configs,
            "config_fingerprints": self.config_fingerprints,
            "results": self.results,
            "metrics": self.metrics,
            "protocol": {k: v.to_dict() for k, v in self.protocol.items()},
            "audit_level": self.audit_level,
            "fn_fingerprint": self.fn_fingerprint,
            "paths": self.paths,
        }


def explore(
    fn: Callable[..., Any],
    configs: Dict[str, Dict[str, Any]],
    replicates: int = 5,
    *,
    seed: Optional[int] = None,
    audit: Literal["calls", "none"] = "calls",
    on_event: Optional[Callable[[Dict[str, Any]], None]] = None,
    progress: bool = True,
    store_root: Optional[str] = None,
) -> Experiment:
    """Run an exploratory experiment.

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
        Times to run each config. Default 5.

    seed : int, optional
        Random seed for reproducibility.

    audit : str
        Audit level: "calls" (track HTTP calls) or "none"

    on_event : Callable, optional
        Callback for live updates.

    progress : bool
        Show progress bar. Default True.

    store_root : str, optional
        Root directory for .crystallize storage

    Returns
    -------
    Experiment
        Results that can be crystallized with a hypothesis.

    Examples
    --------
    >>> exp = explore(
    ...     fn=play_game,
    ...     configs={"baseline": {"x": 1}, "treatment": {"x": 2}},
    ...     replicates=5,
    ... )
    >>> print(exp.hidden_variables().pretty())
    >>> result = exp.crystallize("treatment.win > baseline.win", replicates=20)
    """
    console = Console()

    # Generate IDs
    lineage_id = generate_lineage_id()
    run_id = generate_run_id("explore")

    # Get store
    store = get_store(store_root)

    # Compute config fingerprints
    config_fps = {name: config_fingerprint(cfg) for name, cfg in configs.items()}

    # Get function fingerprint
    fn_fp = fn_fingerprint(fn)

    # Detect function signature
    sig = inspect.signature(fn)
    params = list(sig.parameters.keys())
    wants_ctx = "ctx" in params or len(params) >= 2

    # Print header
    console.print(f"\n[yellow]⚠[/]  [bold]Exploratory mode[/] (run: {run_id})")
    console.print("    When ready to prove something: [cyan]exp.crystallize(\"a.x > b.x\")[/]\n")

    # Emit start event
    if on_event:
        on_event({"type": "start", "run_id": run_id, "configs": list(configs.keys()), "replicates": replicates})

    # Storage
    results: Dict[str, List[Any]] = {name: [] for name in configs}
    metrics: Dict[str, Dict[str, List[Any]]] = {name: {} for name in configs}
    protocol_events: Dict[str, List[Any]] = {name: [] for name in configs}

    total = len(configs) * replicates

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
        disable=not progress,
    ) as pbar:
        task = pbar.add_task("Exploring...", total=total)

        for config_name, config in configs.items():
            cfg_fp = config_fps[config_name]

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
                ctx = create_context(
                    replicate=i,
                    config_name=config_name,
                    config_fingerprint=cfg_fp,
                    config=config,
                    seed=seed,
                    audit=audit,
                )

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

                # Collect protocol events
                protocol_events[config_name].extend(ctx._get_protocol_events())

                # Event: end
                if on_event:
                    on_event({"type": "replicate_end", "config": config_name, "replicate": i, "result": result})

                pbar.advance(task)

    # Build protocol summaries
    protocol_summaries = {
        name: ProtocolSummary.from_events(name, events)
        for name, events in protocol_events.items()
    }

    # Update ledger with explore replicates
    for config_name, cfg_fp in config_fps.items():
        current = store.read_ledger(lineage_id, cfg_fp)
        store.update_ledger(lineage_id, cfg_fp, current + replicates)

    # Build experiment
    experiment = Experiment(
        run_id=run_id,
        lineage_id=lineage_id,
        seed=seed,
        configs=configs,
        config_fingerprints=config_fps,
        results=results,
        metrics=metrics,
        protocol=protocol_summaries,
        audit_level=audit,
        fn_fingerprint=fn_fp,
        fn=fn,
        _store=store,
    )

    # Write explore manifest
    manifest = experiment.to_dict()
    manifest_path = store.write_run_manifest(run_id, manifest)
    experiment.paths["manifest"] = str(manifest_path)

    # Emit end event
    if on_event:
        on_event({"type": "end", "run_id": run_id, "results": results, "metrics": metrics})

    # Print exploratory summary
    console.print("[bold]Results:[/]")
    for config_name, config_metrics in metrics.items():
        if config_metrics:
            console.print(f"  [cyan]{config_name}[/]:")
            for metric_name, values in config_metrics.items():
                mean = sum(values) / len(values) if values else 0
                console.print(f"    {metric_name}: {values} → μ={mean:.2f}")
    console.print()

    return experiment
