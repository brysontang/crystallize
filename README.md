# Crystallize 🧪✨

[![Test](https://github.com/brysontang/crystallize/actions/workflows/test.yml/badge.svg)](https://github.com/brysontang/crystallize/actions/workflows/test.yml)
[![Lint](https://github.com/brysontang/crystallize/actions/workflows/lint.yml/badge.svg)](https://github.com/brysontang/crystallize/actions/workflows/lint.yml)
[![PyPI Version](https://badge.fury.io/py/crystallize-ml.svg)](https://pypi.org/project/crystallize-ml/)
[![Codecov](https://codecov.io/gh/brysontang/crystallize/branch/main/graph/badge.svg)](https://codecov.io/gh/brysontang/crystallize)

⚠️ **Alpha status:** Crystallize ≥0.25.1 is in active development. Interfaces are stable enough for daily use, but minor breaking changes may occur between pre-releases. Install the latest build with:

```bash
pip install --upgrade --pre crystallize-ml
```

---

Crystallize is a lightweight Python framework for running reproducible data-science experiments. It couples immutable execution contexts, deterministic pipeline steps, pluggable execution backends, and first-class statistical verification. Use it either as a Python library or through a fully interactive terminal UI that discovers experiments from declarative `config.yaml` files.

## Why Crystallize?

- **Reproducible by default** – Every run executes inside a `FrozenContext` that records metrics, artifacts, and provenance. The default plugins automatically seed Python’s RNG, persist artifacts, and stream structured logs.
- **Deterministic pipelines** – Build pipelines from `@pipeline_step` factories. Parameter injection pulls values directly from the context, and optional caching skips work when code, parameters, and inputs are unchanged.
- **Treatments & hypotheses** – Express experimental variations with `treatment()` helpers and verify outcomes with `@verifier` + `@hypothesis` pairs.
- **DAG orchestration** – Stitch experiments together with `ExperimentGraph` and reuse artifacts produced by upstream runs.
- **Batteries-included CLI** – Launch `crystallize` for a Textual-powered TUI that scaffolds experiments, runs them live, toggles caching, previews summaries, and opens source files in `$EDITOR`.

## Installation

Crystallize supports Python 3.10+. Install from PyPI:

```bash
pip install --upgrade --pre crystallize-ml
```

Optional extras are published under `crystallize-extras` and can be pulled at once with:

```bash
pip install --upgrade --pre "crystallize-extras[all]"
```

For local development:

```bash
git clone https://github.com/brysontang/crystallize.git
cd crystallize
pip install -e .
```

## Quick Start (Library)

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

The builder ensures the default `ArtifactPlugin`, `SeedPlugin`, and `LoggingPlugin` are attached. Seeds are derived from the replicate index unless you supply a fixed `SeedPlugin(seed=42)`.

See `examples/minimal_experiment/main.py` for a full runnable script with logging enabled.

## Quick Start (CLI)

1. Launch the TUI:
   ```bash
   crystallize
   ```
2. The selection screen discovers every `experiments/**/config.yaml`. Key bindings:
   - `n` create a new experiment scaffold (choose files, optional example code, and reuse outputs from other experiments).
   - `r` refresh discovery, `e` inspect load errors, `q` quit.
   - Highlight an experiment or graph and press `Enter` to open the run screen.
3. Run screen highlights:
   - `R` toggles between **Run** and **Cancel**.
   - `S` jumps to the summary tab; `t` switches the log/summary pane between Rich rendering and plain text.
   - `l` toggles caching for the selected experiment/step, `x` enables or disables individual treatments.
   - `e` opens the highlighted step or experiment in `$CRYSTALLIZE_EDITOR`, `$EDITOR`, or `$VISUAL`.
   - The summary tab lists metrics, hypotheses, and artifacts (with version information) for both current and historical runs.
   - Treatment state (`.state.json`) is persisted so the next run remembers which variants were disabled.

To configure experiments, edit the live `config.yaml` tree in the right pane or open the file in your editor.

## Declarative `config.yaml`

Folder-based experiments mirror the structure used across the examples:

```
experiments/
  └── titanic_survival/
      ├── config.yaml
      ├── datasources.py
      ├── steps.py
      ├── verifiers.py
      └── outputs.py
```

Key sections inside `config.yaml`:

| Section        | Purpose                                                                                         |
| -------------- | ------------------------------------------------------------------------------------------------ |
| `name`         | Overrides the experiment identifier (defaults to folder name).                                   |
| `replicates`   | Baseline and treatment replicate count (default `1`).                                            |
| `cli`          | Controls grouping, priority, icon, color, and visibility in the CLI discovery screen.            |
| `datasource`   | Maps aliases to `@data_source` factories or to `experiment#artifact` references for DAG inputs.  |
| `steps`        | Ordered list of pipeline factories. Dictionaries allow passing keyword arguments.                |
| `outputs`      | Declares named `Artifact` handles. Loader/writer symbols are resolved from `outputs.py`.         |
| `treatments`   | Context values injected before each run. Nested dicts are merged with the baseline context.      |
| `hypotheses`   | Hook into verifier functions defined in `verifiers.py`. Supports multiple metrics per hypothesis.|

Load a folder or individual config with `Experiment.from_yaml(...)` or `ExperimentGraph.from_yaml(...)`. The loader hot-reloads `datasources.py`, `steps.py`, and friends so you can iterate without restarting the CLI.

## Extras

`crystallize-extras` adds optional integrations:

- `RayExecution` – parallelize replicates on a Ray cluster.
- `initialize_ollama_client` / `initialize_async_ollama_client` – populate the context with reusable Ollama clients.
- `OpenAIChatStep` and `VLLMStep` – opinionated pipeline steps for LLM workloads.

Install via `pip install --upgrade --pre "crystallize-extras[ray]"` (or `ollama`, `openai`, `vllm`, `all`).

## Learning More

- **Documentation:** The `/docs` site (Astro + Starlight) mirrors the Diátaxis structure—tutorials, how-to guides, explanations, and API reference. Run `npm install` and `npm run dev` inside `docs/` to preview locally.
- **Examples:** Browse `examples/` for runnable pipelines covering CSV ingestion, DAG chaining, optimization loops, and YAML-driven workflows.
- **Tests:** Unit tests under `tests/` double as usage examples for the CLI, YAML loader, and plugin architecture.

Use [`code2prompt`](https://github.com/mufeedvh/code2prompt) to generate context prompts for large language models:

```bash
code2prompt crystallize \
  --exclude="*.lock" \
  --exclude="**/docs/src/content/docs/reference/*" \
  --exclude="**/package-lock.json" \
  --exclude="**/CHANGELOG.md"
```

## Contributing

Contributions, issues, and feature requests are welcome! Please read [docs/src/content/docs/contributing.md](docs/src/content/docs/contributing.md) for environment setup, testing commands (`pixi run lint`, `pixi run test`, `pixi run cov`, `pixi run diff-cov`), and review guidelines.

## License

Crystallize is distributed under the [Apache 2.0 License](LICENSE).
