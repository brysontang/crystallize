---
title: Creating Custom Plugins
description: Extend Crystallize by hooking into the experiment lifecycle.
---

Crystallize's plugin system lets you modify behavior without subclassing `Experiment`. Plugins inherit from `BasePlugin` and override hook methods to run code at key points.

## Available Hooks

- `init_hook(experiment)`: called during `Experiment.__init__`. Configure default attributes here.
- `before_run(experiment)`: executes at the start of `run()` before any replicates.
- `before_replicate(experiment, ctx)`: invoked before each replicate.
- `after_step(experiment, step, data, ctx)`: called after each pipeline step. Should not mutate `data` or `ctx`.
- `after_run(experiment, result)`: runs after the result object is created.

## Example: Timer Plugin

```python
from crystallize import BasePlugin
import time

class TimerPlugin(BasePlugin):
    def before_run(self, experiment):
        self.start = time.perf_counter()

    def after_run(self, experiment, result):
        duration = time.perf_counter() - self.start
        print(f"Experiment finished in {duration:.2f}s")
```

Use it when constructing the experiment:

```python
exp = Experiment(
    datasource=my_source(),
    pipeline=my_pipeline,
    plugins=[TimerPlugin()],
)
exp.validate()
exp.run()
```
