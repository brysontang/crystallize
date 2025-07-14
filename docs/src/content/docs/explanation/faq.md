---
title: Frequently Asked Questions
description: Common questions about Crystallize and their answers.
---

#### **Q: Why did I get a `ContextMutationError`?**

The `FrozenContext` passed to steps and treatments is immutable. You can **add** new keys with `ctx.add(key, value)` but you cannot overwrite existing ones. Attempting to modify or replace an existing key raises `ContextMutationError` to preserve reproducibility.

#### **Q: Why do I need to use the `ParallelExecution` plugin to run in parallel?**

Crystallize chooses an execution strategy via plugins. Without `ParallelExecution`, experiments run serially using `SerialExecution`. Adding the plugin swaps in a strategy that dispatches replicates concurrently through a thread or process pool.

#### **Q: When should I use a `thread` vs. a `process` executor?**

Use `executor_type="thread"` for I/O-bound pipelines that wait on disk or network. Use `executor_type="process"` for CPU-bound work to bypass Python's GIL. Both options are configured on `ParallelExecution`.

#### **Q: My step isn't being cached. Why?**

Caching works only for steps created with `@pipeline_step(cacheable=True)`. Crystallize hashes the step's code, parameters, and input data. If any of these change—or if parameters or inputs aren't hashable—the cache is skipped and the step reruns.

#### **Q: What is the difference between a Treatment and a Plugin?**

A **Treatment** represents an experimental variable. It modifies the context (by adding keys) so hypotheses can compare outcomes between variations. A **Plugin** hooks into the experiment lifecycle to handle operational concerns like seeding, parallel execution, or saving artifacts. Plugins do not change scientific variables; treatments do.
