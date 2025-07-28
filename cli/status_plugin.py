from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List

from crystallize.plugins.plugins import BasePlugin
from crystallize.utils.constants import BASELINE_CONDITION, CONDITION_KEY, REPLICATE_KEY
from crystallize.utils.context import FrozenContext
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize.experiments.experiment import Experiment

import inspect

STEP_KEY = "step_name"


def emit_step_status(ctx: FrozenContext, percent: float) -> None:
    cb = ctx.get("textual__status_callback")
    if cb:
        # infer the calling function name (usually the step function)
        frame = inspect.currentframe()
        outer = frame.f_back if frame else None
        step_name = ctx.get(STEP_KEY, "<unknown>")
        cb("step", {"step": step_name, "percent": percent})


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
