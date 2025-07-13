---
title: Creating Custom Pipeline Steps
description: How to implement custom steps using the `@pipeline_step` decorator and exit steps.
---

Pipeline steps are the building blocks of a Crystallize **Pipeline**. Each step receives the current data and a `FrozenContext`, then returns the transformed data. The easiest way to create your own step is with the `@pipeline_step` decorator.

## Function-Based Steps

For simpler transformations, decorate a function with `@pipeline_step` to generate a factory. Parameters become keyword arguments when constructing the step.

```python
from crystallize import pipeline_step
from crystallize.core.context import FrozenContext

@pipeline_step(cacheable=True)
def add_constant(data: int, ctx: FrozenContext, value: int = 1) -> int:
    return data + value
```

Instantiate as `add_constant(value=5)` and include it in the pipeline. Setting `cacheable=True` enables hashing of inputs and parameters so results are reused when possible.

```python
from crystallize.core.pipeline import Pipeline

pipeline = Pipeline([add_constant(value=5)])
```

## Exit Steps

Sometimes you want to stop processing early during production inference. Wrap a step with `exit_step()` to mark it as a termination point.

```python
from crystallize.core.pipeline_step import exit_step

pipeline = Pipeline([
    exit_step(add_constant(value=2)),  # pipeline stops after this
    other_step(),                      # remaining steps run only during `run()`
])
```

When `Experiment.apply()` encounters an exit step, it returns the current data immediately. This keeps inference fast while your training pipeline still computes metrics.

## Applying the Best Treatment

After you've run an experiment and identified the winning treatment, you can re-use the pipeline on new data. Pass the treatment name and input data to `experiment.apply()`:

```python
result = experiment.run()
best = result.get_hypothesis("my_hypothesis").ranking["best"]

output = experiment.apply(treatment_name=best, data=[1, 2, 3])
print(output)
```

`apply()` returns the output from the last executed step—or from the exit step if one is encountered—allowing easy integration into production workflows.

## Troubleshooting

- **ContextMutationError**: Attempted to modify an existing key in `FrozenContext`. Use `ctx.add()` with unique keys.
- **Caching not used**: Ensure `cacheable=True` and that your step's outputs depend only on the inputs and parameters.
- **Final metrics missing**: The last step must return a `Mapping[str, Any]` and add metrics via `ctx.metrics.add()` for hypotheses to use.

## Next Steps

- [Tutorials: Building Your First Experiment](/tutorials/basic-experiment/)
- [Reference: PipelineStep](/reference/pipelinestep/)
- [Explanation: Reproducibility](/explanation/reproducibility/)
