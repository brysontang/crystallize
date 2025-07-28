# Crystallize 🧪✨

[![Test](https://github.com/brysontang/crystallize/actions/workflows/test.yml/badge.svg)](https://github.com/brysontang/crystallize/actions/workflows/test.yml)
[![Lint](https://github.com/brysontang/crystallize/actions/workflows/lint.yml/badge.svg)](https://github.com/brysontang/crystallize/actions/workflows/lint.yml)
[![PyPI Version](https://badge.fury.io/py/crystallize-ml.svg)](https://pypi.org/project/crystallize-ml/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/brysontang/crystallize/blob/main/LICENSE)
[![Codecov](https://codecov.io/gh/brysontang/crystallize/branch/main/graph/badge.svg)](https://codecov.io/gh/brysontang/crystallize)

⚠️ Pre-Alpha Notice  
This project is in an early experimental phase. Breaking changes may occur at any time. Use at your own risk.

---

**Rigorous, reproducible, and clear data science experiments.**

Crystallize is an elegant, lightweight Python framework designed to help data scientists, researchers, and machine learning practitioners turn hypotheses into crystal-clear, reproducible experiments.

---

## Why Crystallize?

- **Clarity from Complexity**: Easily structure your experiments, making it straightforward to follow best scientific practices.
- **Repeatability**: Built-in support for reproducible results through immutable contexts, lockfiles, and robust pipeline management.
- **Statistical Rigor**: Hypothesis-driven experiments with integrated statistical verification.

---

## Core Concepts

Crystallize revolves around several key abstractions:

- **DataSource**: Flexible data fetching and generation.
- **Pipeline & PipelineSteps**: Deterministic data transformations. Steps may be
  synchronous or `async` functions and are awaited automatically.
- **Hypothesis & Treatments**: Quantifiable assertions and experimental variations.
- **Statistical Tests**: Built-in support for rigorous validation of experiment results.
- **Optimizer**: Iterative search over treatments using an ask/tell loop.

---

## Getting Started

Crystallize is a powerful framework that can be used in two primary ways: via the interactive **CLI** for managing file-based experiments, or as a **Python library** for full programmatic control.

### Installation

Install the framework and its CLI using pixi:

```bash
pixi install crystallize-ml
```

#### Option 1: The Interactive CLI (Recommended Workflow)

This is the fastest way to create, manage, and run a suite of experiments.

Launch the interactive terminal UI:

```bash
crystallize
```

Scaffold a new experiment:

Inside the UI, press the `n` key to open the "Create New Experiment" screen. Fill out the details to generate a new experiment folder under `experiments/`.

Run your experiment:

The UI will automatically discover your new experiment. Highlight it in the list and press <kbd>Enter</kbd> to run it.

#### Option 2: The Python Library (Programmatic Workflow)

Use the library directly in your Python scripts for advanced use cases and integrations.

```python
from crystallize import (
    Experiment,
    Pipeline,
    Treatment,
    Hypothesis,
    SeedPlugin,
    ParallelExecution,
)

# Define your datasource, pipeline, treatments, etc.
pipeline = Pipeline([...])
datasource = DataSource(...)
treatment = Treatment(...)
hypothesis = Hypothesis(...)

# Build and run the experiment programmatically
experiment = Experiment(
    datasource=datasource,
    pipeline=pipeline,
    plugins=[SeedPlugin(seed=42), ParallelExecution(max_workers=4)],
)
result = experiment.run(
    treatments=[treatment],
    hypotheses=[hypothesis],
    replicates=10,
)
print(result.metrics)
```

### Command Line Interface

The `crystallize` command opens a terminal UI for browsing and executing experiments. Highlight an experiment or graph to view its details and press <kbd>Enter</kbd> to run it. The details panel includes a live config editor so you can adjust values directly in `config.yaml`.

Experiments can define a `cli` section in `config.yaml` to control grouping and style:

```yaml
cli:
  group: 'Data Preprocessing'
  priority: 1
  icon: '📊'
  color: '#85C1E9'
  hidden: false
```

You can also run experiments without the UI:

```bash
python -m experiments.<experiment_name>.main
```

### Project Structure

```
crystallize/
├── datasources/
├── experiments/
├── pipelines/
├── plugins/
└── utils/
```

Key classes and decorators are re-exported in :mod:`crystallize` for concise imports:

```python
from crystallize import Experiment, Pipeline, ArtifactPlugin
```

This layout keeps implementation details organized while exposing a clean, flat public API.

---

## Roadmap

- **Advanced features**: Adaptive experimentation, intelligent meta-learning
- **Collaboration**: Experiment sharing, templates, and community contributions

---

## Contributing

Contributions are very welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Use [`code2prompt`](https://github.com/mufeedvh/code2prompt) to generate LLM-powered docs:

```bash
code2prompt crystallize --exclude="*.lock" --exclude="**/docs/src/content/docs/reference/*" --exclude="**package-lock.json" --exclude="**CHANGELOG.md"
```

---

## License

Crystallize is licensed under the Apache 2.0 License. See [LICENSE](LICENSE) for details.
