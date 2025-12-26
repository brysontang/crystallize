---
title: Parallel Execution Strategies
description: Under-the-hood look at how parallel execution works in Crystallize.
---

Crystallize executes each experiment through an **execution strategy**. The
`Experiment` class delegates the entire replicate loop to a plugin that
implements `run_experiment_loop()`. This keeps the orchestration logic small and
lets users swap in different execution mechanisms without modifying the core
framework.

## Execution Strategy Pattern

During `Experiment.run()`, Crystallize checks the provided plugins for one that
overrides `run_experiment_loop()`. If none is found, the fallback is
`SerialExecution`. The strategy receives two arguments: the `Experiment`
instance and a callable to execute a single replicate. It must return a list of
replicate results in the same order they were submitted.

This pattern cleanly separates **what** happens in a replicate from **how** the
replicates are driven. You can implement custom strategies—perhaps a remote
queue or a distributed system—by creating a plugin that defines this method.

## Built-in Strategies

### SerialExecution

`SerialExecution` is the default single-threaded strategy. It simply iterates
from `0` to `experiment.replicates - 1` and calls the replicate function. It has
an optional `progress` flag that shows a `tqdm` progress bar when multiple
replicates are present. Use this strategy when debugging or when parallelism is
unnecessary.

### ParallelExecution

`ParallelExecution` runs replicates concurrently using Python's
`concurrent.futures` executors. It exposes two key options:

- `executor_type`: either `"thread"` (default) or `"process"`.
- `max_workers`: maximum number of threads or processes in the pool.

The strategy submits each replicate to the chosen executor and collects results
as they complete. Order is preserved by storing the replicate index alongside
its future. The optional `progress` flag works the same as in `SerialExecution`.

> **Warning:** When the `SeedPlugin` is enabled, `executor_type="thread"` reuses
> Python's global RNG state and can interleave seeds between threads. Use
> `executor_type="process"` for any workload that must be reproducible.

## Thread vs. Process Executors

Choosing the right executor type is crucial for performance:

- **Thread executor** (`executor_type="thread"`)
  - Best for I/O-bound workloads: network calls, disk access, or waiting on
    external resources.
  - All threads share the same Python process, so they are limited by the
    Global Interpreter Lock (GIL). CPU-heavy tasks will contend for the GIL and
    may not scale.

- **Process executor** (`executor_type="process"`)
  - Spawns separate Python processes. Each process has its own interpreter and
    bypasses the GIL.
  - Ideal for CPU-bound tasks such as heavy numerical computation.
  - Has higher overhead due to process start-up and data serialization.

Use threads when your pipeline steps mostly perform I/O or release the GIL.
Switch to processes when the steps are CPU-intensive and you need true parallel
execution across cores.

Crystallize computes a sensible default for `max_workers` based on CPU count and
replicate count, but you can override it for fine-tuned control.

## Summary

Parallelism in Crystallize is implemented via pluggable execution strategies.
`SerialExecution` offers a simple baseline, while `ParallelExecution` uses
threads or processes for concurrent replicates. Choose the executor type that
matches your workload to maximize performance.
