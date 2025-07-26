---
title: "How-To: Master Advanced DAG Caching and Execution"
description: An in-depth guide to the resume and rerun strategies and how cache invalidation works in a complex experiment graph.
---

Crystallize executes experiments as a **directed acyclic graph** (DAG). Each experiment stores its artifacts and metrics so future runs can skip work that is already complete. Understanding when the cache is reused and when steps are re-executed is key to running large workflows efficiently.

## Execution Strategies

### `strategy="resume"`
This is the *smart* mode. Before executing each experiment, Crystallize looks for completion markers in the artifact directory. If they exist, the experiment's previous results are loaded and all pipeline steps are skipped. Downstream experiments continue to run normally. Use this for iterative development.

### `strategy="rerun"`
This is the *force* mode. Every experiment is executed from scratch regardless of existing artifacts. Use it when you want completely fresh results or suspect the cache is invalid.

## Understanding Cache Invalidation

With `resume`, an experiment is re-run only if it or any upstream dependency changed. Triggers include:

- Modifying a pipeline step or changing its parameters (its signature changes).
- Altering the treatments attached to an experiment.
- Re-running an upstream experiment which then writes new artifacts.

The tests in `tests/test_experiment_graph.py` demonstrate this behaviour. The `graph_resume_skips_experiments` test runs an experiment once, then runs it again with `strategy="resume"` and confirms no steps are executed a second time:

```python
step_a = CountStep()
plugin = ArtifactPlugin(root_dir=str(tmp_path / "arts"))
exp_a = Experiment(
    datasource=DummySource(),
    pipeline=Pipeline([step_a]),
    plugins=[plugin],
    name="a",
    outputs=[Artifact("x.txt")],
)
...
res = graph2.run(strategy="resume")
assert step_a2.calls == 0
```
【F:tests/test_experiment_graph.py†L143-L187】

## Handling Mixed Replicates

A single upstream replicate can feed many downstream replicates. In `test_mixed_replicates_resume` the first experiment runs once while the second runs ten times. On the second invocation with `resume`, both experiments are skipped and the downstream experiment reuses the single artifact produced by the upstream experiment:

```python
exp_a = Experiment(..., replicates=1)
exp_b = Experiment(..., replicates=10)
...
graph2.run(strategy="resume")
assert step_a2.calls == 0
assert step_b2.calls == 0
```
【F:tests/test_experiment_graph_resume.py†L55-L134】

Crystallize's `Artifact.fetch` automatically selects replicate `0` when an upstream experiment has only one replicate. This allows expensive data generation steps to run once while downstream analysis can run with many replicates without extra work.

## Practical Scenarios

| When to use | Recommended strategy |
| --- | --- |
| Adding a new experiment, modifying a downstream step, or adding treatments | `resume` |
| Changing a core upstream experiment or suspecting corrupted cache | `rerun` |
| Generating a final report with completely fresh results | `rerun` |

By mastering these strategies you can iterate quickly while keeping your artifact storage and compute usage in check.
