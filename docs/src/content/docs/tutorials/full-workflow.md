---
title: The Full Workflow
description: From exploration to production with a single experiment.
---

This capstone tutorial threads together the pieces covered earlier:

1. **Optimise** – search the treatment space programmatically.
2. **Validate** – run enough replicates to confirm the improvement.
3. **Apply** – reuse the winning treatment for single-shot inference.

We reuse the minimal pipeline (`fetch_numbers → add_delta → record_sum`) introduced earlier.

## 1. Optimise

```python
optimizer = GridSearchOptimizer(
    deltas=[-1.0, 0.0, 1.0],
    objective=Objective(metric="sum", direction="minimize"),
)

candidate = experiment.optimize(
    optimizer,
    num_trials=len(optimizer.deltas),
    replicates_per_trial=4,
)
print("Candidate:", candidate.name, candidate._apply_value)
```

Optimisation provides **candidates**, not proof. The helper averages the named metric across replicates and reports it back to the optimiser.

## 2. Validate

```python
result = experiment.run(
    treatments=[candidate],
    hypotheses=[order_by_p_value],
    replicates=40,
)

summary = result.get_hypothesis("order_by_p_value")
print("p-value:", summary.results[candidate.name]["p_value"])
print("significant:", summary.results[candidate.name]["significant"])
```

- Increase replicates until the inference is stable.
- Check the CLI summary tab (`S`) to visually inspect metrics, hypothesis outcomes, and artifacts.

## 3. Apply

Once you trust the treatment, reuse it for single-shot inference:

```python
payload = experiment.apply(candidate)
print("Prediction payload:", payload)
```

`apply()` runs the same pipeline (plugins included) exactly once. Use it in production code or serve it behind an API.

## 4. Persisting Decisions

- Store the treatment parameters (e.g., serialise `candidate` or the config delta) alongside the model release.
- Update your folder-based experiment (`config.yaml`) to include the new treatment so teammates can reproduce the validation run from the CLI.
- Consider writing an ADR if the optimisation introduced architectural changes.

## 5. Automating in the CLI

The CLI focuses on validation and manual runs. A common pattern:

1. Run optimisation from Python to generate a treatment.
2. Update `config.yaml` with that treatment under `treatments:`.
3. Use the run screen to verify results, toggle caching, and inspect artifacts.
4. Record notes directly from the summary tab (copy links to metrics/artifacts).

This workflow keeps exploration scriptable while still benefiting from Crystallize’s live monitoring and provenance capture.
