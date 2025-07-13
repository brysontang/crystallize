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

The core class orchestrating baseline and treatment runs across replicates, followed by hypothesis verification. Configurable via `ExperimentBuilder` for datasource, pipeline, treatments, hypotheses, replicates, and parallelism. Use `run()` for full execution or `apply()` for single-condition inference.

## ExperimentBuilder

A fluent builder for constructing `Experiment` instances. Chain methods like `.datasource()`, `.pipeline()`, `.treatments()`, `.hypotheses()`, `.replicates()`, `.parallel()`, `.max_workers()`, and `.executor_type()`. Call `.build()` to create and validate the experiment.

## Exit Step

A pipeline step marked with `exit_step()` that terminates pipeline execution early, useful for production inference to skip metric computation. Multiple exit steps halt at the first encountered.

## FrozenContext

An immutable dictionary-like object for passing parameters during execution. Supports safe addition of new keys via `add(key, value)` but raises `ContextMutationError` on existing key mutations. Includes a `metrics` attribute for accumulating results.

## Hypothesis

A verifiable assertion about treatment effects, defined by a verifier function, metrics to compare, and a ranker for ordering treatments. Use `@hypothesis(verifier=..., metrics=...)` decorator on ranker functions.

## Immutable Contexts

See _FrozenContext_.

## Metrics

Key-value pairs collected during pipeline execution, stored in `FrozenContext.metrics`. The final pipeline step must return a `Mapping[str, Any]` of metrics. Hypotheses verify differences in aggregated metrics across replicates.

## Parallelism

Optional concurrent execution of replicates using thread or process pools. Set `parallel=True`, `max_workers` (default: CPU count), and `executor_type` ("thread" for I/O-bound, "process" for CPU-bound). Configurable in `Experiment` or `ExperimentBuilder`.

## Pipeline

A sequence of `PipelineStep` objects for deterministic data transformations. The last step must return metrics as `Mapping[str, Any]`. Use `pipeline(*steps)` factory.

## PipelineStep

An abstract class for transformation steps in a pipeline. Implement `__call__(data: Any, ctx: FrozenContext) -> Any` and `params: dict` for hashing. Decorated with `@pipeline_step(cacheable=...)` for factories.

## Ranker

A function in `Hypothesis` that scores verifier results for ranking treatments. Defaults to extracting "p_value" if present.

## Replicates

The number of independent runs of the experiment (default: 1). Aggregates metrics across replicates for statistical power in hypothesis verification.

## Statistical Tests

Verifier functions for hypotheses, often wrapped from libraries like SciPy via `from_scipy(test_func)`. Compare baseline and treatment metric samples.

## Treatment

A named mutation applied to the context for experimental variations. Defined as a mapping of key-values or a callable `apply(ctx: FrozenContext)`. Use `@treatment(name)` decorator.

## Verifier

A function in `Hypothesis` that compares baseline and treatment metrics, returning a result dict (e.g., {"p_value": 0.01, "significant": True}). Decorated with `@verifier` for parameterization.

## FAQ/Troubleshooting

- **Why ContextMutationError?** Attempted to overwrite an existing key in `FrozenContext`. Use new keys for variations.
- **MissingMetricError?** Hypothesis metrics not found in pipeline outputs. Ensure final step emits required keys.
- **Caching not working?** Check `cacheable=True` and consistent hashes (params, inputs).

## Next Steps

- For hands-on setup, see [Tutorials: Getting Started](getting_started.md).
- To customize steps, refer to [How-to Guides: Add a Custom Step](how-to/custom-steps/).
- Detailed API: [Reference: PipelineStep](reference-pipelinestep.md).
