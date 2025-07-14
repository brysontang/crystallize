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
- **Optimizer**: Iterative search over treatments using an ask/tell loop.

---

## Getting Started

### Installation

Crystallize uses `pixi` for managing dependencies and environments:

```bash
pixi install <not-yet-published-package>
```

### Quick Example

```python
from crystallize.core import (
    DataSource,
    Hypothesis,
    Pipeline,
    Treatment,
)
from crystallize.core.experiment import Experiment
from crystallize.core.plugins import SeedPlugin
from crystallize.core.execution import ParallelExecution

# Example setup (simple)
pipeline = Pipeline([...])
datasource = DataSource(...)
t_test = WelchTTest()

@hypothesis(verifier=t_test, metrics="accuracy")
def rank_by_p(result):
    return result["p_value"]

hypothesis = rank_by_p()

treatment = Treatment(name="experiment_variant", apply_fn=lambda ctx: ctx.update({"learning_rate": 0.001}))

experiment = Experiment(
    datasource=datasource,
    pipeline=pipeline,
    treatments=[treatment],
    hypotheses=[hypothesis],
    replicates=3,
    plugins=[SeedPlugin(seed=42), ParallelExecution(max_workers=4)],
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
