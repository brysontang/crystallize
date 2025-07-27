---
title: Chaining Experiments with a DAG
description: Use ExperimentGraph and ExperimentInput to link multiple experiments together.
---

Crystallize can orchestrate complex workflows by chaining experiments in a directed acyclic graph (DAG). Upstream experiments generate artifacts that downstream ones consume.

## 1. Build a Graph

Create an ``ExperimentGraph`` with your experiments and it will infer
dependencies automatically:

```python
from crystallize import ExperimentGraph

graph = ExperimentGraph(exp_a, exp_b)
```

Running `graph.run()` executes experiments in topological order.

## 2. Consume Multiple Artifacts

Combine outputs from several experiments using `ExperimentInput`:

```python
from crystallize import ExperimentInput

ds = ExperimentInput(
    first=exp_a.artifact_datasource(step="StepA", name="output.json"),
    second=exp_b.artifact_datasource(step="StepB", name="output.json"),
)
```

The datasource fetches artifact paths for the current replicate and returns them in a dictionary.

## 3. Example

See [`examples/dag_experiment`](../../../../examples/dag_experiment) for a complete script that averages temperature and humidity data before deriving a comfort index.

You can also scaffold a graph-aware experiment using the interactive CLI. Press
``c`` on the main screen and enable *Use outputs from other experiments*. A
tree lists available experiments. Expand a node to see its outputs and press
<kbd>Space</kbd> to select them. The CLI adds your selections to ``config.yaml``
as ``experiment#output`` strings.

You can load such a workflow directly from the final experiment's YAML file:

```python
from crystallize import ExperimentGraph

graph = ExperimentGraph.from_yaml("experiments/final/config.yaml")
ExperimentGraph.visualize_from_yaml("experiments/final/config.yaml")
```
