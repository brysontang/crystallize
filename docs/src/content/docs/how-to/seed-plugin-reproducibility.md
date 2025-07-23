---
title: How-To: Guarantee Reproducible Results Across Executors
description: Use SeedPlugin with custom seed functions to produce identical metrics in serial, threaded, or process-based runs.
---

Randomness can enter your pipeline through Python's `random` module or through libraries like NumPy. Crystallize's **SeedPlugin** ensures each replicate uses the same seed regardless of the execution strategy. This page walks through creating a custom seed function and verifying deterministic results in parallel.

## 1. Create a Custom Seed Function

The plugin accepts a `seed_fn` that receives the numeric seed for each replicate. Use it to seed all random number generators you rely on:

```python
import random
import numpy as np

from crystallize.plugins.plugins import SeedPlugin


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed % (2**32 - 1))

seed_plugin = SeedPlugin(seed=42, seed_fn=seed_everything)
```

## 2. Define a Stochastic Pipeline

```python
class RandomSource(DataSource):
    def fetch(self, ctx: FrozenContext) -> float:
        return random.random() + np.random.random()

class AddRandomStep(PipelineStep):
    def __call__(self, data, ctx):
        val = data + random.random() + np.random.random()
        ctx.metrics.add("rand", val)
        return {"rand": val}
```

These snippets are taken from the regression test that verifies reproducibility across executors.【F:tests/test_seed_plugin_reproducibility.py†L1-L32】

## 3. Run with Different Executors

```python
from crystallize.plugins.execution import ParallelExecution

exp_serial = Experiment(datasource=RandomSource(), pipeline=Pipeline([AddRandomStep()]), plugins=[seed_plugin])
res_serial = exp_serial.run(replicates=5)

exp_thread = Experiment(
    datasource=RandomSource(),
    pipeline=Pipeline([AddRandomStep()]),
    plugins=[seed_plugin, ParallelExecution(executor_type="thread")],
)
res_thread = exp_thread.run(replicates=5)

exp_process = Experiment(
    datasource=RandomSource(),
    pipeline=Pipeline([AddRandomStep()]),
    plugins=[seed_plugin, ParallelExecution(executor_type="process")],
)
res_process = exp_process.run(replicates=5)

assert res_serial.metrics.baseline.metrics["rand"] == res_thread.metrics.baseline.metrics["rand"] == res_process.metrics.baseline.metrics["rand"]
```

All three execution modes produce exactly the same metrics because the same seed is used for every replicate.

## 4. Best Practices

- Always seed *both* `random` and `numpy.random` if you rely on them.
- When using other libraries (e.g., PyTorch or TensorFlow), seed their RNGs inside your `seed_fn` as well.
- Place `SeedPlugin` first in the plugin list so other plugins and steps see the seeded generators.

Deterministic behavior across executors makes it easy to scale from single-threaded debugging to multi-process production runs without worrying about diverging results.
