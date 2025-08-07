from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List
from pathlib import Path
import json
import time

from crystallize.plugins.plugins import BasePlugin, LoggingPlugin
from crystallize.utils.constants import BASELINE_CONDITION, CONDITION_KEY, REPLICATE_KEY
from crystallize.utils.context import FrozenContext
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize.experiments.experiment import Experiment
from .widgets.writer import WidgetWriter

import inspect
import logging
import contextvars

STEP_KEY = "step_name"


def emit_step_status(ctx: FrozenContext, percent: float) -> None:
    cb = ctx.get("textual__status_callback")
    if cb:
        # infer the calling function name (usually the step function)
        frame = inspect.currentframe()
        outer = frame.f_back if frame else None
        step_name = ctx.get(STEP_KEY, "<unknown>")
        cb("step", {"step": step_name, "percent": percent})


class RichFormatter(logging.Formatter):
    LEVEL_COLORS = {
        "INFO": "[white]",
        "DEBUG": "[dim]",
        "WARNING": "[yellow]",
        "ERROR": "[bold red]",
        "CRITICAL": "[bold white on red]",
    }

    def format(self, record):
        base = super().format(record)
        color = self.LEVEL_COLORS.get(record.levelname, "[white]")
        return f"{color}{base}[/]"


@dataclass
class CLIStatusPlugin(BasePlugin):
    """Track progress of an experiment for the CLI."""

    callback: Callable[[str, dict[str, Any]], None]
    total_steps: int = field(init=False, default=0)
    total_replicates: int = field(init=False, default=0)
    total_conditions: int = field(init=False, default=0)
    completed: int = field(init=False, default=0)
    steps: List[str] = field(init=False, default_factory=list)

    # Add this flag
    sent_start: bool = field(init=False, default=False)
    _step_start: float | None = field(init=False, default=None)
    _records: list[dict[str, Any]] = field(init=False, default_factory=list)

    def before_run(self, experiment: Experiment) -> None:
        # This hook is now only for internal setup, not for callbacks.
        self.completed = 0
        self.sent_start = False
        self._records.clear()

    def before_replicate(self, experiment: Experiment, ctx: FrozenContext) -> None:
        # Move the 'start' event logic here, guarded by the flag
        if not self.sent_start:
            self.steps = [step.__class__.__name__ for step in experiment.pipeline.steps]
            self.total_steps = len(self.steps)
            self.total_replicates = experiment.replicates
            self.total_conditions = len(experiment.treatments) + 1
            self.treatment_names = [
                treatment.name for treatment in experiment.treatments
            ]
            if BASELINE_CONDITION not in self.treatment_names:
                self.treatment_names.insert(0, BASELINE_CONDITION)
            self.callback(
                "start",
                {
                    "steps": self.steps,
                    "treatments": self.treatment_names,
                    "replicates": self.total_replicates,
                    "total": self.total_steps
                    * self.total_replicates
                    * self.total_conditions,
                },
            )
            self.sent_start = True

        # Original before_replicate logic follows
        rep = ctx.get(REPLICATE_KEY, 0) + 1
        condition = ctx.get(CONDITION_KEY, BASELINE_CONDITION)
        if condition == BASELINE_CONDITION:
            self.current_replicate = rep
        self.current_condition = condition
        self.callback(
            "replicate",
            {
                "replicate": getattr(self, "current_replicate", rep),
                "total": self.total_replicates,
                "condition": condition,
            },
        )

        ctx.add("textual__status_callback", self.callback)
        ctx.add("textual__emit", emit_step_status)

    def before_step(self, experiment: Experiment, step: PipelineStep) -> None:  # type: ignore[override]
        self._step_start = time.perf_counter()
        self.callback(
            "step",
            {"step": step.__class__.__name__, "percent": 0.0},
        )

    def after_step(
        self,
        experiment: Experiment,
        step: PipelineStep,
        data: Any,
        ctx: FrozenContext,
    ) -> None:
        if self._step_start is not None:
            duration = time.perf_counter() - self._step_start
            record = {
                "step": step.__class__.__name__,
                "duration": duration,
                "condition": ctx.get(CONDITION_KEY, BASELINE_CONDITION),
                "replicate": ctx.get(REPLICATE_KEY, 0),
            }
            self._records.append(record)
            self._step_start = None
        self.completed += 1
        self.callback(
            "step_finished",
            {
                "step": step.__class__.__name__,
            },
        )

    def after_run(self, experiment: Experiment, result: Any) -> None:  # type: ignore[override]
        prov = (
            result.provenance.get("ctx_changes", {})
            if hasattr(result, "provenance")
            else {}
        )
        errors = getattr(result, "errors", {})
        skip_runs: set[tuple[str, int]] = set()
        for key in errors:
            if "_rep_" not in key:
                continue
            cond, rep_str = key.rsplit("_rep_", 1)
            cond_name = BASELINE_CONDITION if cond == "baseline" else cond
            try:
                rep_idx = int(rep_str)
            except ValueError:
                continue
            skip_runs.add((cond_name, rep_idx))

        counters: dict[tuple[str, int], int] = {}
        cache_dir = Path.home() / ".cache" / "crystallize" / "steps"
        cache_dir.mkdir(parents=True, exist_ok=True)
        hist_file = cache_dir / f"{experiment.name}.json"
        hist_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            history = json.loads(hist_file.read_text())
        except Exception:
            history = {}

        for rec in self._records:
            cond = rec["condition"]
            rep = rec["replicate"]
            if (cond, rep) in skip_runs:
                continue
            idx = counters.get((cond, rep), 0)
            cache_hit = False
            step_prov = prov.get(cond, {}).get(rep, [])
            if idx < len(step_prov):
                cache_hit = bool(step_prov[idx].get("cache_hit", False))
            counters[(cond, rep)] = idx + 1
            if cache_hit:
                continue
            step_name = rec["step"]
            history.setdefault(step_name, []).append(rec["duration"])

        hist_file.write_text(json.dumps(history))


exp_var = contextvars.ContextVar("exp_name", default="-")
step_var = contextvars.ContextVar("step_name", default="-")


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.exp = exp_var.get()
        record.step = step_var.get()
        return True


class WidgetLogHandler(logging.Handler):
    """Logging.Handler that forwards records to a WidgetWriter."""

    def __init__(self, writer: WidgetWriter, level=logging.NOTSET):
        super().__init__(level)
        self.writer = writer

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            # non-blocking: Textual must update from the UI thread
            self.writer.write(msg + "\n")
        except Exception:  # pragma: no cover
            self.handleError(record)


@dataclass
class TextualLoggingPlugin(LoggingPlugin):
    writer: WidgetWriter | None = None
    handler_cls: type[logging.Handler] = WidgetLogHandler

    def before_run(self, experiment):
      super().before_run(experiment)
      if not self.writer:
          return

      logger = logging.getLogger("crystallize")

      # Ensure exactly one ContextFilter
      logger.filters = [f for f in logger.filters if not isinstance(f, ContextFilter)]
      logger.addFilter(ContextFilter())

      # Remove all existing handlers to avoid stale widget bindings
      logger.handlers = []

      # Attach a fresh widget handler
      handler = self.handler_cls(self.writer)
      fmt = "%(asctime)s  %(levelname).1s  %(exp)-10s  %(step)-18s | %(message)s"
      datefmt = "%H:%M:%S"
      handler.setFormatter(RichFormatter(fmt, datefmt=datefmt))
      logger.addHandler(handler)

      # Prevent propagation to the root logger
      logger.propagate = False
    
    
    def before_step(self, experiment: Experiment, step: PipelineStep) -> None:
        exp_var.set(experiment.name)
        step_var.set(step.__class__.__name__)

    def after_run(self, experiment: Experiment, result: Any) -> None:
        super().after_run(experiment, result)

        logger = logging.getLogger("crystallize")
        for h in [h for h in logger.handlers if isinstance(h, self.handler_cls)]:
            try:
                h.close()
            finally:
                logger.removeHandler(h)

        logger.propagate = False

        if self.writer and hasattr(self.writer, "close"):
            self.writer.close()
