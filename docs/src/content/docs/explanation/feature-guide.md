---
title: Feature Guide
---

A deep dive into why Crystallize's features are designed the way they are.

## Datasources: Why Not Just Pass Config?

You might wonder why we have `@data_source` decorated functions instead of just passing config objects:

```python
# Why this?
@data_source
def baseline_config(ctx: FrozenContext) -> GameConfig:
    return GameConfig(models=["llama3:8b"] * 6)

# Instead of this?
config = GameConfig(models=["llama3:8b"] * 6)
```

**The answer: context-aware configuration.**

Datasources receive the experiment context, so they can:

```python
@data_source
def adaptive_config(ctx: FrozenContext) -> GameConfig:
    # Vary config based on replicate number
    replicate = ctx.get("replicate", 0)

    # Or based on treatment parameters
    model = ctx.get("model_override", "llama3:8b")

    return GameConfig(models=[model] * 6)
```

This enables treatments that modify config without duplicating datasource logic.

---

## Pipeline Steps: Why Decorators?

```python
@pipeline_step()
def run_game(config: GameConfig, ctx: FrozenContext) -> GameResult:
    ...
```

The decorator provides:

1. **Automatic context injection**: `ctx` is populated with replicate number, treatment name, seed, etc.
2. **Lifecycle hooks**: Plugins can run `before_step` and `after_step`
3. **Error handling**: Failed steps are caught and recorded, not crash the experiment
4. **Artifact tracking**: `ctx.artifacts` persists between steps

Without it, you'd manually pass context through every function call.

---

## Treatments: The Missing Piece

**Current limitation**: Treatments mutate context, but don't swap datasources.

```python
# This works - adds values to context
Treatment("high_temp", {"temperature": 1.5})

# This doesn't work (yet)
Treatment("dolphin", datasource=dolphin_config)  # Not supported
```

**Workaround**: Have datasource read from context:

```python
@data_source
def flexible_config(ctx: FrozenContext) -> GameConfig:
    model = ctx.get("model", "llama3:8b")  # Treatment can override
    return GameConfig(models=[model] * 6)

# Then treatment sets context
Treatment("dolphin", {"model": "dolphin-llama3:latest"})
```

**New in this release**: String-based datasource references with the registry:

```python
from crystallize import data_source, get_datasource

@data_source("training_data", register=True)
def load_data(ctx):
    return my_data()

# Later, without importing:
ds = get_datasource("training_data")
```

---

## Plugins: Separation of Concerns

Plugins handle cross-cutting concerns so your experiment code stays focused:

### SeedPlugin
```python
SeedPlugin(seed=42, auto_seed=True)
```
- Sets base seed for reproducibility
- `auto_seed=True`: Each replicate gets `seed + replicate * 31337`
- Handles numpy, random, torch seeding automatically

### LoggingPlugin
```python
LoggingPlugin(verbose=True, log_level="INFO")
```
- Configures the `crystallize` logger
- Logs experiment start/end, step completion, errors
- `verbose=True`: Logs every step completion

### ArtifactPlugin
```python
ArtifactPlugin(root_dir="./data", versioned=True)
```
- Saves `ctx.artifacts` to disk after each step
- `versioned=True`: Creates `v0`, `v1`, etc. directories
- Auto-prunes old versions to save space

### Execution Plugins
```python
ParallelExecution(max_workers=4)  # Multiprocessing
AsyncExecution(max_workers=4)     # Asyncio
SerialExecution()                  # Default, one at a time
```
- Control how replicates run
- Parallel is great for independent runs
- Serial for debugging or resource-constrained environments

---

## FrozenContext: Immutability as a Feature

```python
ctx.add("key", value)      # OK - add new key
ctx["key"] = new_value     # ERROR - can't mutate existing
ctx.override(key=value)    # OK - explicit override for special cases
```

**Why immutable?**

1. **Reproducibility**: If context could change mid-experiment, results would be non-deterministic
2. **Debugging**: "What was the value at step 3?" has one answer
3. **Parallelism**: No race conditions on shared state

The `override()` method exists for legitimate cases (like treatments modifying baseline parameters) but requires explicit intent.

---

## Metrics: Why `ctx.metrics.add()` Instead of Return Values?

```python
# Option A: Return metrics
def run_game(config, ctx):
    state = game.run()
    return {"win": state.winner == "aligned", "rounds": state.round_number}

# Option B: Add to context (what Crystallize does)
def run_game(config, ctx):
    state = game.run()
    ctx.metrics.add("win", 1 if state.winner == "aligned" else 0)
    ctx.metrics.add("rounds", state.round_number)
    return state
```

**Option B wins because:**

1. **Steps can add metrics incrementally**: Not everything is known at return time
2. **Metrics aggregate automatically**: Crystallize collects across replicates
3. **Return value is for data flow**: Pass state to next step, metrics are metadata

**New: `ctx.record()` with tags**:
```python
ctx.record("outcome", 1, tags={"winner": "aligned", "model": "llama3"})
```
Tags enable richer analysis without polluting metric names.

---

## Hypotheses: Statistical Testing Built In

```python
from crystallize import hypothesis

@hypothesis(
    metric="win",
    direction="maximize",
    test="fisher_exact"
)
def alignment_improves_wins(baseline, treatment):
    # Returns True if treatment is significantly better
    return treatment.mean() > baseline.mean()
```

Hypotheses run after all replicates complete and compare treatments to baseline.

**Why separate from pipeline?**
- Hypotheses need aggregate data (all replicates)
- Pipeline steps see one replicate at a time
- Clean separation: data collection vs. analysis

---

## Result Persistence

Results can be saved for later analysis:

```python
result = experiment.run()

# Save to JSON
result.to_json("experiment_results.json")

# Or get as string
json_str = result.to_json()

# Save to Parquet for pandas analysis
result.to_parquet("experiment_results.parquet")

# Convert to dict
data = result.to_dict()
```

---

## Standalone Context

For testing pipeline steps outside of experiments:

```python
from crystallize import standalone_context

# No need to create MockContext or FrozenContext manually
ctx = standalone_context({"input_data": [1, 2, 3]})

# Now test your step
result = my_step(ctx)

# Check metrics
ctx.record("accuracy", 0.95, tags={"model": "v1"})
```

This eliminates boilerplate when debugging or unit testing individual steps.
