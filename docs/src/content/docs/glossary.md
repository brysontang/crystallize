---
title: Glossary
description: A glossary of key terms and acronyms used in the Crystallize framework.
---

This glossary provides definitions for key terms and acronyms used in the Crystallize framework. Definitions are designed to be clear, self-contained, and precise, facilitating understanding for both human users and large language models (LLMs). Terms are listed alphabetically.

## Caching

A mechanism in Crystallize that stores intermediate results of pipeline steps to ensure reproducibility and efficiency. Cacheable steps (default: `cacheable=True`) compute hashes of inputs and parameters, reusing outputs when hashes match. Non-cacheable steps (e.g., stochastic processes) bypass caching. Cache files are stored in `.cache/` (configurable via `CRYSTALLIZE_CACHE_DIR`).

## DataSource

An abstract class for fetching or generating input data for experiments. Implement the `fetch(ctx: FrozenContext) -> Any` method to produce data based on the immutable context. Decorated with `@data_source` for parameterized factories.

Example:

```python
from crystallize import data_source
from crystallize.core.context import FrozenContext

@data_source
def csv_source(ctx: FrozenContext, path: str) -> list:
    # Load CSV from path
    return [...]  # Return data list
```

## Experiment

The core class orchestrates baseline and treatment runs across replicates, followed by hypothesis verification. Configure it directly with your datasource, pipeline, treatments, hypotheses, replicates, and a list of plugins. Use `run()` for full execution or `apply()` for single-condition inference.


## Exit Step

A pipeline step marked with `exit_step()` that terminates pipeline execution early, useful for production inference to skip metric computation. Multiple exit steps halt at the first encountered.

## FrozenContext

An immutable dictionary-like object for passing parameters during execution. Supports safe addition of new keys via `add(key, value)` but raises `ContextMutationError` on existing key mutations. Includes a `metrics` attribute for accumulating results.

## Hypothesis

A verifiable assertion about treatment effects, defined by a verifier function, metrics to compare, and a ranker for ordering treatments. Use `@hypothesis(verifier=..., metrics=...)` decorator on ranker functions.

## Immutable Contexts

See _FrozenContext_.

## Metrics

Key-value pairs collected during pipeline execution, stored in `FrozenContext.metrics`. Steps call `ctx.metrics.add()` to record values that hypotheses later verify. The last step may return any data type.

## Parallelism
Optional concurrent execution of replicates using thread or process pools. Configure via the `ExecutionPlugin` with `parallel`, `max_workers` (default: CPU count), and `executor_type` ("thread" for I/O-bound, "process" for CPU-bound).

## Pipeline
A sequence of `PipelineStep` objects for deterministic data transformations. Use `pipeline(*steps)` to build them. Metrics are added to the context during execution; returning them is optional.

## PipelineStep

An abstract class for transformation steps in a pipeline. Implement `__call__(data: Any, ctx: FrozenContext) -> Any` and `params: dict` for hashing. Decorated with `@pipeline_step(cacheable=...)` for factories.

## Ranker

A function in `Hypothesis` that scores verifier results for ranking treatments. Defaults to extracting "p_value" if present.

## Replicates

The number of independent runs of the experiment (default: 1). Aggregates metrics across replicates for statistical power in hypothesis verification.

## Statistical Tests

Verifier functions for hypotheses, typically built with the `@verifier` decorator. They compare baseline and treatment metric samples and may call into SciPy or other libraries.

## Treatment

A named mutation applied to the context for experimental variations. Defined as a mapping of key-values or a callable `apply(ctx: FrozenContext)`. Use `@treatment(name)` decorator.

## Verifier

A function in `Hypothesis` that compares baseline and treatment metrics, returning a result dict (e.g., {"p_value": 0.01, "significant": True}). Decorated with `@verifier` for parameterization.

## Plugin

An object subclassing `BasePlugin` that hooks into the experiment lifecycle. Plugins configure or observe experiments by implementing one or more hook methods.

## BasePlugin

The abstract base class defining available hooks: `init_hook`, `before_run`, `before_replicate`, `after_step`, and `after_run`.

## Hook

A method on a plugin invoked at specific points during experiment execution. Hooks enable customization without subclassing `Experiment` itself.

## FAQ/Troubleshooting

- **Why ContextMutationError?** Attempted to overwrite an existing key in `FrozenContext`. Use new keys for variations.
- **MissingMetricError?** Hypothesis metrics not found in pipeline outputs. Ensure steps call `ctx.metrics.add` with the required names.
- **Caching not working?** Check `cacheable=True` and consistent hashes (params, inputs).

## Next Steps

- For hands-on setup, see [Tutorials: Getting Started](getting_started.md).
- To customize steps, refer to [How-to Guides: Add a Custom Step](how-to/custom-steps/).
- For experiment configuration, see [How-to Guides: Customizing Experiments](how-to/customizing-experiments/).
- Detailed API: [Reference: PipelineStep](reference-pipelinestep.md).
