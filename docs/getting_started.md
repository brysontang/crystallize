# Getting Started with Crystallize

Crystallize helps you run reproducible, hypothesis-driven experiments. This guide walks through installation, the two primary ways to use the framework (CLI and Python API), and where to find runnable examples.

## Requirements

- Python 3.10+
- Optional: [pixi](https://pixi.sh) for reproducible dev environments
- Optional extras (`crystallize-extras`) when integrating Ray, OpenAI, vLLM, or Ollama

## Install

```bash
# Latest alpha build
pip install --upgrade --pre crystallize-ml

# Extras bundle (optional)
pip install --upgrade --pre "crystallize-extras[all]"
```

For development:

```bash
git clone https://github.com/brysontang/crystallize.git
cd crystallize
pip install -e .
```

If you use pixi, run `pixi install` to create the managed environment and expose helper tasks (`pixi run lint`, `pixi run test`, `pixi run cov`, `pixi run diff-cov`).

## Option 1 – Terminal UI

```bash
crystallize
```

- The selection screen discovers every `experiments/**/config.yaml`. Use `n` to scaffold a new experiment, `r` to refresh, `e` to review load errors, and `q` to quit.
- Press `Enter` on an experiment or graph to open the run screen. There you can toggle caching (`l`), enable/disable treatments (`x`), jump to the summary tab (`S`), or open highlighted code in `$EDITOR` (`e`).
- The summary tab lists metrics, hypotheses, and artifacts for the latest run, including versioned history if the `ArtifactPlugin` is configured with `versioned=True`.
- Treatment state is persisted in `config.state.json` so your next run keeps the same toggles.

## Option 2 – Python API

The `crystallize` package re-exports the core abstractions. The snippet below mirrors `examples/minimal_experiment/main.py`:

```python
from crystallize import (
    Experiment,
    Pipeline,
    ParallelExecution,
    FrozenContext,
    data_source,
    pipeline_step,
    treatment,
    hypothesis,
    verifier,
)
from scipy.stats import ttest_ind

@data_source
def source(ctx: FrozenContext) -> list[int]:
    return [0, 0, 0]

@pipeline_step()
def add_delta(data: list[int], ctx: FrozenContext, *, delta: float = 0.0) -> list[float]:
    return [x + delta for x in data]

@pipeline_step()
def record_metric(data: list[float], ctx: FrozenContext):
    return data, {"total": sum(data)}

add_ten = treatment("add_ten", {"delta": 10.0})

@verifier
def welch_t_test(baseline, treatment, alpha: float = 0.05):
    stat, p_value = ttest_ind(
        treatment["total"], baseline["total"], equal_var=False
    )
    return {"p_value": p_value, "significant": p_value < alpha}

@hypothesis(verifier=welch_t_test(), metrics="total")
def by_p_value(result: dict[str, float]) -> float:
    return result.get("p_value", 1.0)

experiment = (
    Experiment.builder("demo")
    .datasource(source())
    .add_step(add_delta())
    .add_step(record_metric())
    .plugins([ParallelExecution(max_workers=4)])
    .treatments([add_ten()])
    .hypotheses([by_p_value])
    .replicates(10)
    .build()
)

result = experiment.run()
print(result.get_hypothesis("by_p_value").results)
```

The builder attaches the default `ArtifactPlugin`, `SeedPlugin`, and `LoggingPlugin`. Override them—or change execution strategy entirely—by passing your own plugin list.

## YAML Workflows

To declaratively configure experiments, create a folder containing `config.yaml` plus supporting modules (`datasources.py`, `steps.py`, `outputs.py`, `verifiers.py`). Load it from code or from the CLI:

```python
from pathlib import Path
from crystallize import Experiment, ExperimentGraph

exp = Experiment.from_yaml(Path("experiments/my_experiment/config.yaml"))
graph = ExperimentGraph.from_yaml(Path("experiments"))
```

- The loader hot-reloads Python files so iterative changes appear on the next run.
- Artifacts declared under `outputs:` are available as parameters annotated with `Artifact` in your pipeline steps.
- Referencing `other_experiment#artifact_name` under `datasource:` automatically wires up cross-experiment dependencies in an `ExperimentGraph`.

## Explore the Examples

| Folder                          | Highlights                                                                  |
| ------------------------------ | ---------------------------------------------------------------------------- |
| `examples/minimal_experiment`  | End-to-end experiment with treatments, hypothesis, and context metrics.     |
| `examples/optimization_experiment` | Illustrates the ask/tell optimizer interface.                          |
| `examples/yaml_experiment`     | Complete folder-driven workflow for the CLI.                                |
| `examples/folder_experiment`   | Demonstrates `Experiment.from_yaml` and `ExperimentGraph.visualize_from_yaml`. |

Each example ships with a `README` or inline comments describing how to run it.

## Next Steps

- Browse the tutorials and how-to guides under `docs/src/content/docs`.
- Regenerate the API reference after code changes with `python3.10 generate_docs.py`.
- When building new capabilities, capture the rationale in an ADR (see `docs/adr/`).
