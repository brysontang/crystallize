### Crystallize – Framework Overview

**Repository root:** `crystallize/`  
**Python requirement:** 3.10+  
**Current version:** 0.25.1 (alpha)  
**Primary entry points:** the `crystallize` package and the `crystallize` CLI (Textual TUI)

---

## Core Building Blocks

| Module                                | Responsibility                                                                                                         |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `crystallize.datasources`             | Datasource primitives. `@data_source` factories create deterministic providers; `Artifact` exposes typed artifact IO.   |
| `crystallize.pipelines`               | `Pipeline` orchestrates ordered `PipelineStep` instances created with `@pipeline_step`. Supports caching & setup hooks. |
| `crystallize.experiments`             | `Experiment`, `ExperimentBuilder`, `ExperimentGraph`, treatments, hypotheses, optimizers, results, and provenance.      |
| `crystallize.plugins`                 | Execution plugins (`SerialExecution`, `ParallelExecution`, `AsyncExecution`) plus default `SeedPlugin`, `LoggingPlugin`, `ArtifactPlugin`. |
| `crystallize.utils`                   | Immutable `FrozenContext`, caching utilities, dependency injection, custom exceptions, constants.                       |

Top-level imports re-export the most common abstractions:

```python
from crystallize import (
    Experiment,
    ExperimentGraph,
    ExperimentBuilder,
    Pipeline,
    PipelineStep,
    FrozenContext,
    DataSource,
    Artifact,
    Treatment,
    Hypothesis,
    SeedPlugin,
    ParallelExecution,
    data_source,
    pipeline_step,
    treatment,
    verifier,
    hypothesis,
    resource_factory,
)
```

The builder attaches default plugins that seed the Python RNG, stream structured logs, and persist artifacts to `data/<experiment>/vN/...`.

---

## Running Experiments Programmatically

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

Key behaviours:

- `FrozenContext` enforces immutability. Use `ctx.add(...)` to append keys, `ctx.metrics.add(name, value)` to record outputs, and `ctx.artifacts.add(name, bytes)` to persist files.
- `@pipeline_step` injects keyword-only parameters from the context when not provided explicitly. A step may return `data` or `(data, metrics_dict)`.
- `SeedPlugin` seeds Python’s RNG per replicate using `seed_fn` (customisable for NumPy/JAX).
- `Experiment.apply(...)` runs a single replicate (useful for production inference).
- `Experiment.aoptimize(...)` and `Experiment.optimize(...)` implement an ask/tell loop for parameter searches (`BaseOptimizer` + `Objective`).

---

## YAML-Driven Workflows

Folder layout (see `examples/yaml_experiment/`):

```
my_experiment/
├── config.yaml
├── datasources.py
├── steps.py
├── outputs.py          # optional
└── verifiers.py        # optional
```

`config.yaml` example:

```yaml
name: my_experiment
replicates: 20
cli:
  group: Feature Experiments
  priority: 2
  icon: "🧪"
datasource:
  raw: load_dataset          # loads from datasources.py
steps:
  - preprocess
  - {score_model: {artifact: model_blob}}
outputs:
  model_blob:
    file_name: model.pkl
    loader: load_pickle      # optional function from outputs.py
    writer: dump_pickle
treatments:
  baseline: {}
  tuned:
    learning_rate: 0.05
hypotheses:
  - name: effectiveness
    verifier: welch_t
    metrics: overall_score
```

Loading:

```python
from pathlib import Path
from crystallize import Experiment, ExperimentGraph

exp = Experiment.from_yaml(Path("my_experiment/config.yaml"))
graph = ExperimentGraph.from_yaml(Path("experiments/"))
result = graph.run()
```

Implementation details:

- Pipeline parameters annotated with `Artifact` are automatically wired to entries declared under `outputs:`. The loader/writer functions are looked up in `outputs.py`.
- Cross-experiment dependencies use the `experiment_name#artifact_name` syntax inside `datasource:`. When present, the loader builds an `ExperimentGraph`.
- Config discovery honours the optional `cli.hidden` flag and stores per-experiment state under `config.state.json` to remember toggled treatments.

---

## Textual CLI (`crystallize`)

Selection screen:

- Discovers every `config.yaml` below the current working directory.
- Groups experiments/graphs by `cli.group`, sorted by `cli.priority`.
- Key bindings: `n` (create scaffold), `r` (refresh), `e` (view load errors), `q` (quit). `Enter` opens the run screen.

Run screen:

- Left sidebar shows experiment and step trees; caching (`l`) toggles step-by-step or whole-experiment caching by flipping `PipelineStep.cacheable`.
- Treatment pane lets you enable/disable variants (`x`). Choices persist via the `.state.json` file next to the config.
- Header displays live progress, estimated time remaining, active replicate, and treatment.
- Tabs: `Logs` (rich and plain-text toggle via `t`), `Summary` (metrics, hypotheses, artifact table with versioning and historical metrics), `Errors`.
- `R` toggles Run/Cancel; `S` jumps to summary; `e` opens the highlighted node’s source using `$CRYSTALLIZE_EDITOR`, `$EDITOR`, or `$VISUAL`.

Create Experiment modal:

- Select standard files (`steps.py`, `datasources.py`, `outputs.py`, `verifiers.py`) and optionally embed example code scaffolds.
- Graph mode lets you pull declared outputs from existing experiments and wire them into a new DAG.

---

## Extras Package (`crystallize-extras`)

- **RayExecution** (`crystallize_extras.ray_plugin.RayExecution`): parallelise replicates on a Ray cluster. Import raises informative error if `ray` is missing.
- **Ollama client factory** (`initialize_ollama_client`, `initialize_async_ollama_client`): pipeline steps that seed the context with reusable Ollama clients using `resource_factory`.
- **OpenAI / vLLM steps**: ready-made async/sync steps for LLM inference that leverage context-managed clients.

Install with `pip install --upgrade --pre "crystallize-extras[ray]"` (or `[openai]`, `[ollama]`, `[vllm]`, `[all]`).

---

## Tests & Tooling

- `tests/test_from_yaml.py` exercises the YAML loader, artifact wiring, and `ExperimentGraph`.
- `tests/test_run_screen.py` and `tests/test_run_screen_cache.py` cover CLI keystrokes, caching toggles, treatment persistence, and summary rendering.
- `tests/test_eta.py` validates ETA calculations and progress callbacks for the CLI status plugin.
- `tests/test_treatment_panel.py` checks treatment toggling logic and state persistence.

Commands (pixi features):

```bash
pixi run lint        # ruff check crystallize tests
pixi run test        # pytest -q
pixi run cov         # pytest --cov=crystallize --cov-report=xml
pixi run diff-cov    # diff-cover coverage.xml --compare-branch=main
```

`generate_docs.py` uses Lazydocs to refresh the Markdown API reference under `docs/src/content/docs/reference/`. Run it with Python 3.10 after modifying the public API.

---

## Experimentation Philosophy

Crystallize nudges toward lean, reproducible experimentation:

- Keep changes isolated—each treatment should alter exactly one lever so attribute shifts remain clear.
- Use paired replicates (same seeds) when possible; fall back to unpaired tests only when the setup forces it.
- Record 1–2 guardrail metrics up front (latency, cost, safety) and enforce them before optimising primary metrics.
- Document rationale via ADRs for any significant architectural choice (`docs/adr/00xx-*.md`).

The default plugins log start/end times, active treatments, seeds, and aggregate hypothesis rankings to make review easy.
