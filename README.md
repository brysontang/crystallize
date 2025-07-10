# Crystallize 🧪✨

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
- **Pipeline & PipelineSteps**: Deterministic data transformations.
- **Hypothesis & Treatments**: Quantifiable assertions and experimental variations.
- **Statistical Tests**: Built-in support for rigorous validation of experiment results.

---

## Getting Started

### Installation

Crystallize uses `pixi` for managing dependencies and environments:

```bash
pixi install <not-yet-published-package>
```

### Quick Example

```python
from crystallize.core import Experiment, Pipeline, DataSource

# Example setup (simple)
pipeline = Pipeline([...])
datasource = DataSource(...)
hypothesis = Hypothesis(metric="accuracy", direction="increase", statistical_test=WelchTTest())

treatment = Treatment(name="experiment_variant", apply_fn=lambda ctx: ctx.update({"learning_rate": 0.001}))

experiment = (
    Experiment()
    .with_pipeline(pipeline)
    .with_datasource(datasource)
    .with_treatments([treatment])
    .with_hypotheses([hypothesis])
    .with_replicates(3)
)
experiment.validate()

result = experiment.run()
print(result.metrics)
print(result.hypothesis_result)
```

---

## Roadmap

- **Advanced features**: Adaptive experimentation, intelligent meta-learning
- **Collaboration**: Experiment sharing, templates, and community contributions

---

## Contributing

Contributions are very welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

Crystallize is licensed under the Apache 2.0 License. See [LICENSE](LICENSE) for details.
