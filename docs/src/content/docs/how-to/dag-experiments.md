---
title: Chaining Experiments with a DAG
description: Feed artifacts from one experiment into another with ExperimentGraph.
---

Crystallize represents workflows as a directed acyclic graph. Nodes are regular `Experiment` instances; edges pass artifacts between them.

## 1. Publish Outputs Upstream

```yaml
# producer/config.yaml
outputs:
  summary:
    file_name: summary.json
    writer: dump_json
    loader: load_json
steps:
  - produce_summary
```

- The loader/writer functions live in `outputs.py`.
- Pipeline steps accept artifacts by annotating parameters with `Artifact` (see the CLI tutorial for a full example).

## 2. Consume Them Downstream

Reference upstream outputs using `experiment#artifact` inside your downstream `config.yaml`:

```yaml
# consumer/config.yaml
datasource:
  producer_summary: producer#summary
steps:
  - inspect_summary
```

When the consumer runs, the datasource returns a dictionary whose values are the loader outputs (`load_json(...)` in this example).

## 3. Run the Graph Programmatically

```python
from crystallize import ExperimentGraph

graph = ExperimentGraph.from_yaml("experiments/consumer/config.yaml")
result = graph.run()
```

`ExperimentGraph.from_yaml` inspects the folder hierarchy, finds dependencies, and executes them in topological order. The returned dictionary maps experiment name to `Result`.

## 4. Using the CLI

- `n` opens **Create New Experiment**. Enable **Use outputs from other experiments** to select artifacts from existing folders. Each selection adds an `experiment#artifact` entry under `datasource:`.
- Graph experiments display a `📈` icon and show dependencies in the run screen. When you run the downstream node, the CLI executes prerequisites first.

## 5. Combining Multiple Outputs

If you need more control, construct an `ExperimentInput` manually:

```python
from crystallize import ExperimentInput

ds = ExperimentInput(
    summary=producer.artifact_datasource(step="Produce_SummaryStep", name="summary.json"),
    metrics=analytics.artifact_datasource(step="WriteMetricsStep", name="metrics.csv"),
)
consumer_experiment.datasource = ds
```

`ExperimentInput` bundles multiple datasources and ensures replicate counts align when artifacts share the same upstream experiment.

## 6. Visualising

```python
ExperimentGraph.visualize_from_yaml("experiments/consumer/config.yaml")
```

The helper renders a Graphviz diagram (requires Graphviz installed) showing experiment dependencies—handy for large workflows.

## 7. Troubleshooting

- **Missing artifact** – Ensure upstream experiments ran with `ArtifactPlugin` and that the `file_name`/step names match. The CLI error panel lists the missing path.
- **Replicate mismatch** – If upstream artifacts have different replicate counts, update the producer configuration or homogenise the data before chaining.
- **Loader returns bytes** – Provide a `loader` function in `outputs.py` to decode bytes into richer objects.
