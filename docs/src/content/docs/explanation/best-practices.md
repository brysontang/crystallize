---
title: "Explanation: Design Patterns & Best Practices"
description: A guide to structuring robust and scalable Crystallize projects.
---

When your project grows beyond a single script, adopting a clear structure and a few core habits makes Crystallize easier to maintain and scale.

## Structuring Your Project

Organise your code by responsibility. A typical layout might look like:

```text
project/
├── datasources/
├── steps/
├── experiments/
└── graph.py
```

Each experiment imports datasources and pipeline steps from the dedicated modules. The `graph.py` file defines the `ExperimentGraph` that ties them together.

## Managing Expensive Resources with `resource_factory`

Some objects, such as large ML models or database connections, cannot be pickled and are expensive to initialise. Wrap the construction function with `resource_factory` and add it to your experiment's `initial_ctx`.

```python
factory = resource_factory(
    OpenAiClientFactory(opts),  # your initialization callable
    key="openai_client",
)
ctx.add("openai_client", factory)
```

This pattern mirrors the initialisation helpers in `crystallize_extras.openai_step`. The factory ensures that the resource is created once per worker process, so parallel runs share memory efficiently and avoid pickling errors.

## Writing Idempotent and Cacheable Pipeline Steps

A pipeline step should produce the same output when given the same input and context. Avoid in-place modifications of shared objects and use a seed from the context for all randomness:

```python
seed = ctx.get("seed_used")
random.seed(seed)
np.random.seed(seed % (2**32 - 1))
```

Keeping steps deterministic allows the `resume` strategy to reliably reuse cached artifacts and only rerun stages that have truly changed.

## Effective Naming Conventions

Choose clear, consistent names so artifacts are easy to interpret:

- Experiments: `exp_01_data_prep`
- Treatments: `treatment_upsample_2x`
- Metrics: `metric_f1_score_macro`

Meaningful names help track results across replicates and over time.
