from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List

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

    def before_run(self, experiment: Experiment) -> None:
        # This hook is now only for internal setup, not for callbacks.
        self.completed = 0
        self.sent_start = False

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

    def after_step(
        self,
        experiment: Experiment,
        step: PipelineStep,
        data: Any,
        ctx: FrozenContext,
    ) -> None:
        self.completed += 1
        percent = 0.0
        total = self.total_steps * self.total_replicates * self.total_conditions
        if total:
            percent = self.completed / total
        self.callback(
            "step_finished",
            {
                "step": step.__class__.__name__,
            },
        )


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

        logger = logging.getLogger("crystallize")
        if not any(isinstance(h, ContextFilter) for h in logger.filters):
            logger.addFilter(ContextFilter())

        # ① DROP any previously-installed StreamHandlers
        logger.handlers = [
            h
            for h in logger.handlers
            if isinstance(h, self.handler_cls)  # keep existing Widget handler
        ]

        # ② Add / re-add Widget handler if missing
        if self.writer and not any(
            isinstance(h, self.handler_cls) for h in logger.handlers
        ):
            handler = self.handler_cls(self.writer)
            fmt = "%(asctime)s  %(levelname).1s  %(exp)-10s  %(step)-18s | %(message)s"
            datefmt = "%H:%M:%S"  # short, no date
            handler.setFormatter(RichFormatter(fmt, datefmt=datefmt))
            logger.addHandler(handler)

        # ③ Make sure nothing bubbles up to the root logger
        logger.propagate = False

    def before_step(self, experiment: Experiment, step: PipelineStep) -> None:
        exp_var.set(experiment.name)
        step_var.set(step.__class__.__name__)
