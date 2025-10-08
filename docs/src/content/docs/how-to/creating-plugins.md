---
title: Creating Custom Plugins
description: Hook into the experiment lifecycle to add custom behaviour.
---

Plugins inherit from `crystallize.plugins.plugins.BasePlugin` and override lifecycle hooks. They are attached to an `Experiment` via the `plugins` argument or appended when using `Experiment.builder()`.

## 1. Lifecycle Hooks

| Hook | When it fires |
| ---- | ------------- |
| `init_hook(experiment)` | Immediately after the experiment is initialised. Useful for injecting default treatments or outputs. |
| `before_run(experiment)` | Right before replicates start. Configure loggers, allocate resources, etc. |
| `before_replicate(experiment, ctx)` | Before each pipeline execution. The immutable `ctx` already contains baseline/treatment info. |
| `before_step(experiment, step)` | Prior to invoking a pipeline step. |
| `after_step(experiment, step, data, ctx)` | After a step returns. Avoid mutating `data` or `ctx`; emit telemetry instead. |
| `after_run(experiment, result)` | Once metrics and provenance are finalised. |
| `run_experiment_loop(experiment, replicate_fn)` | Optional: override to replace the entire replicate loop (e.g., distribute via Ray). Return `NotImplemented` to fall back to the default serial runner. |

## 2. Example: Timing Plugin

```python
from crystallize.plugins.plugins import BasePlugin
import time

class TimerPlugin(BasePlugin):
    def before_run(self, experiment):
        self._start = time.perf_counter()

    def after_run(self, experiment, result):
        duration = time.perf_counter() - self._start
        experiment.get_plugin(LoggingPlugin)  # optional – reuse existing loggers
        print(f"{experiment.name or 'experiment'} finished in {duration:.2f}s")
```

Attach it:

```python
experiment = Experiment(
    datasource=my_source(),
    pipeline=Pipeline([...]),
    plugins=[TimerPlugin()],
)
experiment.run()
```

## 3. Example: Custom Replicate Loop

```python
class PrintPlugin(BasePlugin):
    def run_experiment_loop(self, experiment, replicate_fn):
        results = []
        for rep in range(experiment.replicates):
            print(f"Running replicate {rep}")
            results.append(replicate_fn(rep))
        return results
```

Return `NotImplemented` from `run_experiment_loop` if you want the default behaviour for some cases.

## 4. CLI Integration

The TUI injects two plugins when starting a run:

- `CLIStatusPlugin` streams progress updates to the UI.
- `TextualLoggingPlugin` replaces standard logging so Rich-formatted logs appear in the interface.

The CLI checks whether your experiment has already attached these classes to avoid duplicates. Understanding this pattern helps when you want to integrate Crystallize with other tooling (e.g., send status updates to Slack).

## 5. Testing Plugins

- Use the `tests/plugins` pattern in the repository: create a minimal experiment and assert side effects inside the plugin.
- When your plugin depends on per-replicate state, leverage `FrozenContext.metrics` or `ctx.get("replicate")`.
- For long-lived resources, close them in `after_run`.
