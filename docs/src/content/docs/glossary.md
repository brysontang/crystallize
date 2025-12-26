---
title: Glossary
description: A glossary of key terms and acronyms used in the Crystallize framework.
---

This glossary provides definitions for key terms and acronyms used in the Crystallize framework. Definitions are designed to be clear, self-contained, and precise, facilitating understanding for both human users and large language models (LLMs). Terms are listed alphabetically.

## Agentic Harness

A spec-first bounded synthesis framework built on top of the core Crystallize APIs. Enables safe execution of LLM-generated code within sandboxed environments. The harness provides pipeline steps for claim specification, code synthesis with import/syntax validation, capsule execution with resource limits, and metamorphic property testing.

## Bounded Synthesis

The process of generating code within strict constraints defined by a `Spec`. The synthesized code is validated via AST analysis to ensure it only imports allowed modules, avoids dangerous calls (`eval`, `exec`, `open`), and doesn't attempt privilege escalation via dunder attributes.

## Caching

A mechanism in Crystallize that stores intermediate results of pipeline steps to ensure reproducibility and efficiency. Steps are opt-in (`@pipeline_step(cacheable=True)`). When enabled, hashes of the step definition, explicit parameters, and input data decide whether to reuse previous outputs. Cache files reside in `.cache/` (configurable via `CRYSTALLIZE_CACHE_DIR`).

## Capsule

An isolated subprocess environment for executing synthesized code safely. The capsule enforces resource limits (CPU time, memory, file size), import guards, and module diffing to detect unauthorized behavior. Code runs with a restricted `__builtins__` containing only safe functions.

## Claim

A frozen dataclass (`crystallize.agentic.Claim`) representing a desired improvement or behavior to verify. Contains an `id`, human-readable `text` description, and `acceptance` criteria dictionary. Claims flow through the agentic pipeline and are recorded in evidence bundles for provenance.

## DataSource

An abstract class for fetching or generating input data for experiments. Implement the `fetch(ctx: FrozenContext) -> Any` method to produce data based on the immutable context. Decorated with `@data_source` for parameterized factories.

Example:

```python
from crystallize import data_source
from crystallize import FrozenContext

@data_source
def csv_source(ctx: FrozenContext, path: str) -> list:
    # Load CSV from path
    return [...]  # Return data list
```

## EvidenceBundlePlugin

A plugin that creates comprehensive audit trails for agentic workflows. After each run, it persists a JSON bundle linking claims → specs → generated code → execution outputs → hypothesis verdicts. Bundles are saved to `{artifact_dir}/{experiment_id}/v{version}/{condition}/evidence/bundle.json`.

## Experiment

The core class orchestrates baseline and treatment runs across replicates, followed by hypothesis verification. Configure it directly with your datasource, pipeline, treatments, hypotheses, replicates, and a list of plugins. Use `run()` for full execution or `apply()` for single-condition inference.


## FrozenContext

An immutable dictionary-like object for passing parameters during execution. Supports safe addition of new keys via `add(key, value)` but raises `ContextMutationError` on existing key mutations. Includes a `metrics` attribute for accumulating results.

## Hypothesis

A verifiable assertion about treatment effects, defined by a verifier function, metrics to compare, and a ranker for ordering treatments. Use `@hypothesis(verifier=..., metrics=...)` decorator on ranker functions.

## Metamorphic Testing

A testing technique that validates code behavior by applying transformations to input data and checking that certain properties (invariants) still hold. In the agentic harness, `run_metamorphic_tests` applies transforms like `permute_rows` and compares metrics between baseline and transformed executions. Useful for validating that aggregations are order-independent.

## Metrics

Key-value pairs collected during pipeline execution, stored in `FrozenContext.metrics`. Steps call `ctx.metrics.add()` to record values that hypotheses later verify. The last step may return any data type.

## Parallelism
Optional concurrent execution of replicates using thread or process pools. Configure via the `ParallelExecution` plugin with `max_workers` (default: CPU count) and `executor_type` ("thread" for I/O-bound, "process" for CPU-bound).

## Pipeline
A sequence of `PipelineStep` objects for deterministic data transformations. Create one with `Pipeline([step_a(), step_b()])` or via the `@pipeline` decorator. Steps may add metrics to the context or return `(data, metrics_dict)`.

## PipelineStep

An abstract class for transformation steps in a pipeline. Implement `__call__(data: Any, ctx: FrozenContext) -> Any` and `params: dict` for hashing. Decorated with `@pipeline_step(cacheable=...)` for factories.

## PromptProvenancePlugin

A plugin that tracks all LLM calls made during agentic synthesis. Collects prompt/response metadata recorded via `record_llm_call()` and persists them to `{artifact_dir}/{experiment_id}/v{version}/{condition}/prompts/llm_calls.json`. Works alongside `EvidenceBundlePlugin` for complete provenance.

## Ranker

A function in `Hypothesis` that scores verifier results for ranking treatments. Defaults to extracting "p_value" if present.

## Replicates

The number of independent runs of the experiment (default: 1). Aggregates metrics across replicates for statistical power in hypothesis verification.

## Spec

A frozen dataclass (`crystallize.agentic.Spec`) defining execution constraints for bounded synthesis. Contains `allowed_imports` (module allowlist), `properties` (metamorphic invariants to test), `contracts` (reserved), and `resources` (time/memory limits). The spec is validated before code execution and enforced at runtime.

## Statistical Tests

Verifier functions for hypotheses, typically built with the `@verifier` decorator. They compare baseline and treatment metric samples and may call into SciPy or other libraries.

## Treatment

A named mutation applied to the context for experimental variations. Defined as a mapping of key-values or a callable `apply(ctx: FrozenContext)`. Use `@treatment(name)` decorator.

## Verifier

A function in `Hypothesis` that compares baseline and treatment metrics, returning a result dict (e.g., {"p_value": 0.01, "significant": True}). Decorated with `@verifier` for parameterization.

## Plugin

An object subclassing `BasePlugin` that hooks into the experiment lifecycle. Plugins configure or observe experiments by implementing one or more hook methods.

## BasePlugin

The abstract base class defining available hooks: `init_hook`, `before_run`, `before_replicate`, `before_step`, `after_step`, `after_run`, and (optionally) `run_experiment_loop` for custom execution strategies.

## Hook

A method on a plugin invoked at specific points during experiment execution. Hooks enable customization without subclassing `Experiment` itself.

## FAQ/Troubleshooting

- **Why ContextMutationError?** Attempted to overwrite an existing key in `FrozenContext`. Use new keys for variations.
- **MissingMetricError?** Hypothesis metrics not found in pipeline outputs. Ensure steps call `ctx.metrics.add` with the required names.
- **Caching not working?** Check `cacheable=True` and consistent hashes (params, inputs).

## Next Steps

- For hands-on setup, see [Tutorials: Getting Started](/tutorials/intro/).
- To customize steps, refer to [How-to: Creating Custom Steps](/how-to/custom-steps/).
- For experiment configuration, see [How-to: Customizing Experiments](/how-to/customizing-experiments/).
- Detailed API: [Reference: PipelineStep](/reference/pipeline_step/).
