---
title: Honest Feedback (and Roadmap)
---

Real friction points from actual usage, and what we're doing about them.

## What Made Me Reach for Scripts Instead

### 1. The Datasource/Treatment Gap (biggest one)

When I wanted "run baseline, then run with Dolphin models" - the mental model is "same experiment, different config." But treatments mutate context, they don't swap datasources. So I wrote `main.py` with a `CONFIGS` dict and a for-loop.

```python
# What I wanted
experiment.add_treatment("dolphin", datasource=dolphin_config)

# What I did instead
for config_name in ["baseline", "dolphin_spoilers"]:
    results[config_name] = run_games(CONFIGS[config_name], n)
```

**Status**: Partially addressed with datasource registry and context-aware datasources. Full treatment-datasource binding is on the roadmap.

### 2. The "One Quick Run" Problem

I constantly want to run ONE game to see what happens. Crystallize assumes replicates. I end up doing:

```python
# What I do
python -c "from games import AlignmentLab; AlignmentLab().run_game(verbose=True)"

# What would be nice
crystallize run-once social_deception --verbose
```

**Status**: `standalone_context()` helps with testing steps. Full `debug()` mode coming.

### 3. Live Visibility

Games take 60+ seconds. I want to watch. The plugin hooks are `before_step`/`after_step`, but interesting events happen DURING steps. I had to thread event handlers through `config → game → emitter`.

A `ctx.emit(event)` that plugins could subscribe to would be cleaner.

**Status**: On the roadmap.

---

## What Would Add Leverage

### 1. First-class "debug mode"
```python
experiment.debug(treatment="dolphin")  # Runs 1 replicate, verbose, no parallelism
```

### 2. Resume from failure
```python
experiment.run(resume=True)  # Skips completed replicates
```
Right now if replicate 8/10 crashes, you restart from 0.

### 3. Streaming results
```python
for result in experiment.stream():
    print(f"Replicate {result.replicate}: {result.metrics}")
    # I can see progress, cancel early, etc.
```

### 4. Config diffing
```bash
$ crystallize diff baseline dolphin_spoilers
- hallucination_models: ["llama3:8b", "llama3:8b"]
+ hallucination_models: ["dolphin-llama3:latest", "dolphin-llama3:latest"]
```

### 5. Interactive CLI
```bash
$ crystallize run social_deception --replicates 3 --treatment dolphin_spoilers
# Override without editing YAML
```

---

## The Decision Point

**I reach for Crystallize when:**
- Running 5+ replicates
- Comparing 2+ treatments
- I'll want these results next week
- Reproducibility matters

**I stay in script-land when:**
- "Does this even work?"
- Debugging one specific case
- Don't know what metrics matter yet
- Iterating on game mechanics

The gap is the **transition**. I start with a script, get something working, then face "do I refactor into Crystallize or keep hacking?" If that migration was smoother (import my functions, Crystallize wraps them), I'd switch earlier.

---

## The On-Ramp: `quick_experiment()`

```python
from crystallize import quick_experiment

results = quick_experiment(
    fn=run_game,
    configs={"baseline": config1, "treatment": config2},
    replicates=5
)
# Returns dict of results, no YAML, no classes
```

That's the on-ramp. Graduate to full `Experiment` class when you need plugins/hypotheses/artifacts.

**Status**: Implemented in this release.
