from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, List

from crystallize.plugins.plugins import BasePlugin
from crystallize.utils.constants import BASELINE_CONDITION, CONDITION_KEY, REPLICATE_KEY
from crystallize.utils.context import FrozenContext
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize.experiments.experiment import Experiment

import json
import time

STEP_KEY = "step_name"


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
    step_start: float | None = field(init=False, default=None)
    _progress_events: list[tuple[float, float]] = field(init=False, default_factory=list)

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
        ctx.add("textual__emit", self.emit_step_status)

    def before_step(
        self, experiment: Experiment, step: PipelineStep, ctx: FrozenContext
    ) -> None:
        self.step_start = time.perf_counter()
        self._progress_events = [(self.step_start, 0.0)]

    def after_step(
        self,
        experiment: Experiment,
        step: PipelineStep,
        data: Any,
        ctx: FrozenContext,
    ) -> None:
        if self.step_start is not None:
            duration = time.perf_counter() - self.step_start
            self._record_duration(experiment, step.__class__.__name__, duration)
            self.step_start = None
        self._progress_events = []
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

    def _record_duration(
        self, experiment: Experiment, step_name: str, duration: float
    ) -> None:
        exp_name = experiment.name or experiment.id
        cache_dir = Path.home() / ".cache" / "crystallize" / "steps"
        cache_dir.mkdir(parents=True, exist_ok=True)
        path = cache_dir / f"{exp_name}.json"
        try:
            data = json.loads(path.read_text())
        except FileNotFoundError:
            data = {}
        data.setdefault(step_name, []).append(duration)
        path.write_text(json.dumps(data))

    def emit_step_status(self, ctx: FrozenContext, percent: float) -> None:
        cb = ctx.get("textual__status_callback")
        if not cb:
            return
        step_name = ctx.get(STEP_KEY, "<unknown>")
        eta: float | None = None
        if self.step_start is not None:
            now = time.perf_counter()
            self._progress_events.append((now, percent))
            events = self._progress_events[-5:]
            if len(events) >= 2:
                dt = events[-1][0] - events[0][0]
                dp = events[-1][1] - events[0][1]
                if dt > 0 and dp > 0:
                    rate = dp / dt
                    eta = (1 - percent) / rate
        info: dict[str, Any] = {"step": step_name, "percent": percent}
        if eta is not None:
            info["eta"] = eta
        cb("step", info)
