---
title: Scaling with Replicates and Parallelism
description: Increase statistical power without waiting longer than necessary.
---

Crystallize separates **how many times** an experiment runs (replicates) from **how** those runs execute (serial, threaded, async, or multi-process). This tutorial shows how to tune both knobs and understand the trade-offs.

## 1. Replicates

Replicates drive statistical power. Increase them when verifiers need more samples.

```python
result = experiment.run(replicates=32)
len(result.metrics.baseline.metrics["total"])   # → 32
```

- Replicates apply to the baseline and every active treatment.
- You can override the default replicates on the experiment (`Experiment(..., replicates=16)`) and still pass a different value for a single run.
- Provenance captures the replicate count (`result.provenance["replicates"]`).

## 2. Execution Plugins

```python
from crystallize import SerialExecution, ParallelExecution, AsyncExecution

Experiment(
    datasource=fetch_numbers(),
    pipeline=Pipeline([...]),
    plugins=[ParallelExecution(max_workers=4, executor_type="process")],
)
```

| Plugin              | Use when…                                                                 | Notes                                                                 |
| ------------------- | ------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `SerialExecution`   | You want deterministic, single-threaded execution (default fallback).     | No configuration required.                                            |
| `ParallelExecution` | Steps are CPU-bound or you need multiple processes/threads per replicate. | `executor_type="process"` bypasses the GIL; `"thread"` suits IO work. |
| `AsyncExecution`    | Pipeline steps are async functions (e.g., HTTP calls) and you want an event loop per experiment. | Step factories can be `async def`; Crystallize awaits them automatically. |

Implementation details:

- `ParallelExecution` delegates to `concurrent.futures`. Whatever you pass must be picklable when using processes.
- The CLI exposes an execution strategy picker for DAGs. Within the TUI run screen the top bar displays the current strategy (`resume` for cached, `rerun` when caching disabled).
- If a plugin implements `run_experiment_loop`, the default serial loop is bypassed. Extras (`RayExecution`) use this hook to distribute replicates across a Ray cluster.

## 3. Combining Replicates and Parallelism

```python
experiment = (
    Experiment.builder("scaling_demo")
    .datasource(fetch_numbers())
    .add_step(add_delta())
    .add_step(expensive_step())           # imagine this takes ~1s
    .plugins([ParallelExecution(max_workers=8, executor_type="process")])
    .treatments([boost_total()])
    .replicates(40)
    .build()
)

experiment.run()
```

Tips:

- Start with `max_workers` equal to the number of logical cores for CPU-bound work. Measure first; some workloads saturate earlier.
- Use the CLI summary tab to check elapsed time per replicate. When caching is on, avoided steps appear with a lock icon.
- For stochastic steps, consider disabling caching (`l` in the run screen) so reruns do not reuse stale outputs.

## 4. Async Pipelines

Async steps are declared the same way; the decorator adds an `__acall__` coroutine behind the scenes.

```python
@pipeline_step()
async def fetch_remote(data: dict, ctx: FrozenContext):
    async with httpx.AsyncClient() as client:
        resp = await client.get(data["url"])
        return resp.json()

experiment = (
    Experiment.builder("async_demo")
    .datasource(fetch_urls())
    .add_step(fetch_remote())
    .plugins([AsyncExecution()])
    .replicates(5)
    .build()
)
```

`AsyncExecution` spins up an event loop per experiment, awaits each step, and still supports plugins (hooks run around `await` boundaries).

## 5. Monitoring from the CLI

- The run screen shows replicate progress, ETA (computed via an exponential moving average), and per-step state.
- `l` toggles caching, which also flips the experiment’s strategy between `"resume"` and `"rerun"`.
- Treatment toggles persist so you can benchmark multiple strategies back-to-back without editing YAML.

## 6. Troubleshooting

- **Pickling errors** with `ParallelExecution(executor_type="process")`: ensure pipeline steps and datasources are top-level callables or decorated factories. Use `resource_factory` for objects that cannot be pickled directly.
- **No speedup**: If your steps are IO-bound, switch to `executor_type="thread"` or `AsyncExecution`. If they are extremely short, the overhead of parallelism may dominate.
- **Shared state**: Remember the context is immutable. Store shared caches via `resource_factory` or attach them to a plugin; never mutate module-level globals during parallel runs.
