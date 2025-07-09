# Crystallize Core Components Documentation

Welcome to the Crystallize framework! This document provides a quick overview of core abstractions and how they fit together to form reproducible and statistically rigorous data science experiments.

---

## 📦 Core Components

### 1. **DataSource**

Abstract class for fetching or generating data.

- **Method:** `fetch(ctx: FrozenContext) -> Any`
- Implementations: CSV loader, synthetic data generator, API fetcher

---

### 2. **PipelineStep**

Abstract class for a deterministic transformation of data.

- **Method:** `__call__(data: Any, ctx: FrozenContext) -> Any`
- **Property:** `params` (for caching/provenance)

---

### 3. **Pipeline**

Sequential container of `PipelineStep` instances.

- **Method:** `run(data: Any, ctx: FrozenContext) -> Mapping[str, Any]`
- Ensures final step returns a metrics dictionary.

---

### 4. **FrozenContext**

Immutable execution context for provenance and reproducibility.

- Raises `ContextMutationError` on attempts to overwrite existing keys.
- Allows adding new keys safely.

---

### 5. **Experiment**

Core orchestrator of experiment execution.

- Executes baseline and treatment pipelines across replicates.
- Aggregates metrics and verifies hypotheses.

---

### 6. **Treatment**

Named configuration variations applied to experiments.

- **Method:** `apply(ctx: FrozenContext)`
- Adds parameters or overrides hyperparameter spaces.

---

### 7. **Hypothesis**

Quantifiable assertion verified post-experiment.

- Uses `StatisticalTest` for verification.
- Determines if experiment results confirm hypothesis.

---

### 8. **StatisticalTest**

Abstract class encapsulating statistical tests (e.g., t-tests, ANOVA).

- **Method:** `run(baseline: Mapping, treatment: Mapping, alpha: float) -> dict`
- Returns significance and p-value results.

---

### 9. **Result**

Captures metrics, artifacts, errors, and provenance.

- Offers helper methods for easy access to experiment outcomes.

---

## 🚀 Next Steps

With these components, you're ready to build, run, and verify rigorous experiments. Explore implementations of DataSources, PipelineSteps, Treatments, and StatisticalTests to get started quickly!
