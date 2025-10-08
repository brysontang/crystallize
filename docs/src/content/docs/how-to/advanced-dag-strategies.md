---
title: "How-To: Advanced DAG Caching"
description: Understand the resume/rerun strategies and when cached artifacts are reused.
---

Crystallize stores every run under `data/<experiment>/vN/`. The completion marker `.crystallize_complete` and accompanying `metadata.json` allow later runs to skip work. Two strategies control this behaviour.

## 1. Strategies

| Strategy | Behaviour |
| -------- | --------- |
| `"rerun"` (default) | Always execute the experiment, ignoring cached artifacts. |
| `"resume"` | If the latest run completed (baseline + all active treatments) and artifacts are still present, load metrics and artifacts instead of re-running. |

You can set the strategy per experiment (`experiment.strategy = "resume"`) or pass `strategy="resume"` to `Experiment.run()` / `ExperimentGraph.run()`.

## 2. When Does Resume Re-run?

Even under `resume`, Crystallize re-executes an experiment when:

- The pipeline signature changes (code edits or new parameters).
- Treatments differ from the cached run (new names or different apply payloads).
- Upstream dependencies rerun and publish new artifacts.
- The completion marker or metadata is missing.

These rules are covered by the test suite (`tests/test_experiment_graph.py`, `tests/test_experiment_graph_resume.py`).

## 3. Mixed Replicates

Artifact metadata stores the replicate count of the producing experiment. When a downstream experiment has more replicates than the upstream producer, `Artifact.fetch` cycles indices so replicate `i` reads `i % upstream_replicates`. This lets you generate expensive artifacts once and reuse them many times.

## 4. Example: Skipping Work

```python
graph = ExperimentGraph.from_yaml("experiments/consumer/config.yaml")

# First run produces artifacts
graph.run(replicates=10)

# Second run loads existing results
graph.run(strategy="resume")
```

Use logging (or the CLI) to confirm that steps are skipped: cached steps show lock icons in the run screen, and plugins such as `LoggingPlugin(verbose=True)` emit messages when resume loads stored metrics.

## 5. Manual Cache Controls

- Delete `data/<experiment>` to force a full rerun.
- Toggle caching for specific steps in the CLI (`l` on the run screen) to recompute only the parts you care about.
- Set `ArtifactPlugin(versioned=True, artifact_retention=N)` to keep multiple runs and prune older ones automatically.

Understanding these knobs keeps large DAGs responsive while guaranteeing fresh results when you change code or configuration.
