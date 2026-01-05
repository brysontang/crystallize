---
title: Why Crystallize?
---

## The Problem

You're running experiments. Maybe ML training runs, maybe A/B tests, maybe (like us) AI social deception games. You start with a simple script:

```python
results = []
for i in range(10):
    result = run_experiment()
    results.append(result)
print(f"Win rate: {sum(results)/len(results)}")
```

Then reality hits:
- "Can we compare this to the baseline?"
- "What seed did we use for that good run?"
- "The results were different yesterday - what changed?"
- "Can we run treatments in parallel?"
- "Where did we save those metrics?"

You end up with `experiment_v3_final_FINAL.py` and a spreadsheet of manually copied numbers.

## What Crystallize Does

Crystallize is the scaffolding that grows with your experiments:

### 1. Replicates with Reproducibility

```python
experiment = Experiment(
    datasource=my_config,
    pipeline=[run_game],
    replicates=10,
    plugins=[SeedPlugin(seed=42)]
)
```

Every replicate gets a deterministic seed derived from the base seed. Six months later, you can reproduce run #7 exactly.

### 2. Treatments as First-Class Citizens

Instead of commenting/uncommenting code:

```python
# Bad: The "toggle comments" approach
# config = baseline_config()
config = treatment_config()  # USING THIS ONE
```

Crystallize runs all conditions systematically:

```python
experiment.treatments = [
    Treatment("dolphin_spoilers", {"model": "dolphin-llama3"}),
    Treatment("gemma_prey", {"model": "gemma3"}),
]
# Runs baseline + all treatments, compares automatically
```

### 3. Metrics That Travel With Results

```python
@pipeline_step()
def run_game(config, ctx):
    state = game.run()

    # Metrics are bound to this replicate, this treatment
    ctx.metrics.add("win", 1 if state.winner == "aligned" else 0)
    ctx.metrics.add("rounds", state.round_number)

    return state
```

No more "which column was that in the spreadsheet?"

### 4. Statistical Comparison Built In

```python
result = experiment.run()

# Crystallize aggregates across replicates automatically
baseline_win_rate = result.metrics.baseline.metrics["win"]  # [0,1,1,0,1,...]
treatment_win_rate = result.metrics.treatments["dolphin"].metrics["win"]

# Hypotheses can run statistical tests
# Fisher's exact, t-tests, etc.
```

### 5. Plugins for Cross-Cutting Concerns

Seeding, logging, artifact storage, parallel execution - these aren't your experiment's job:

```python
plugins = [
    SeedPlugin(seed=42, auto_seed=True),
    LoggingPlugin(verbose=True),
    ArtifactPlugin(root_dir="./data", versioned=True),
    ParallelExecution(max_workers=4),
]
```

Your experiment code stays focused on the science.

---

## Real Example: AI Social Deception

We built a Mafia-style game where AI models deceive each other. The research question: *Does RLHF training enable social intelligence?*

**Without Crystallize:**
```python
# run_experiment.py - 200 lines of boilerplate
# results_v2.csv - manually updated
# "I think we ran 5 games? Or was it 10?"
```

**With Crystallize:**
```python
experiment = Experiment(
    name="social_deception",
    datasource=baseline_config,  # All Llama3
    pipeline=[run_alignment_lab],
    replicates=5,
)

experiment.treatments = [
    Treatment("dolphin_vs_llama", dolphin_config),
    Treatment("dolphin_vs_gemma", gemma_config),
]

result = experiment.run()
# Automatic: seeding, metrics collection, treatment comparison
```

**What we learned:**
- Baseline (Llama3 vs Llama3): 80% "bad guy" wins
- Dolphin vs Llama3: 80% "bad guy" wins
- Dolphin vs Gemma: 100% "bad guy" wins

The framework made it trivial to add new treatments and get comparable results. When we pivoted to a "Birthday Surprise" variant (prosocial framing), we just added new datasources and reused the same pipeline.

---

## When NOT to Use Crystallize

- **One-off scripts**: If you're running something once, just run it
- **Production systems**: Crystallize is for research/experimentation, not serving
- **Hyperparameter optimization**: Use Optuna/Ray Tune (though Crystallize can wrap them)

---

## Philosophy

1. **Convention over configuration**: Sensible defaults that you can override
2. **Composition over inheritance**: Plugins add capabilities, don't subclass
3. **Research-first**: Optimize for iteration speed and reproducibility, not production performance
4. **Data stays with code**: Metrics, artifacts, and configs live together

The goal: spend time on your experiment, not your experiment infrastructure.
