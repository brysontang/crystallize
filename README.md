# Crystallize

**From Play to Proof.**

Run experiments. Start exploring, then crystallize your findings with a hypothesis.

```bash
pip install crystallize-ml
```

## Quick Start

### Exploratory Mode

Just play around. No ceremony.

```python
from crystallize import run

def play_game(config, ctx):
    # Your logic here
    winner = "treatment" if config["power"] > 5 else "baseline"
    ctx.record("win", 1 if winner == "treatment" else 0)
    return {"winner": winner}

results = run(
    fn=play_game,
    configs={
        "weak": {"power": 2},
        "strong": {"power": 10},
    },
    replicates=5,
)
```

Output:
```
⚠  Exploratory mode — perfect for playing around.
   When ready to prove something: hypothesis="a.x > b.x"

Results:
  weak:
    win: [0, 0, 0, 0, 0] → μ=0.00
  strong:
    win: [1, 1, 1, 1, 1] → μ=1.00
```

### Confirmatory Mode

You noticed something. Now prove it.

```python
results = run(
    fn=play_game,
    configs={
        "weak": {"power": 2},
        "strong": {"power": 10},
    },
    replicates=20,
    hypothesis="strong.win > weak.win",
    seed=42,
)
```

Output:
```
✓ Confirmatory mode
  Hypothesis: strong.win > weak.win
  Seed: 42

✓ Hypothesis SUPPORTED
  strong.win (μ=1.00, n=20) > weak.win (μ=0.00, n=20)
  Effect size: 1.00, p=0.000
```

## The API

```python
from crystallize import run

results = run(
    fn=my_function,           # Your function: fn(config) or fn(config, ctx)
    configs={...},            # {"name": {config_dict}, ...}
    replicates=10,            # How many times to run each config
    seed=42,                  # For reproducibility
    hypothesis="a.x > b.x",   # Triggers confirmatory mode
    on_event=callback,        # For live UIs (viewer integration)
    progress=True,            # Show progress bar
)
```

### Recording Metrics

```python
def my_function(config, ctx):
    result = do_something(config)

    # Record metrics for analysis
    ctx.record("accuracy", result.accuracy)
    ctx.record("latency", result.latency, tags={"unit": "ms"})

    return result
```

### Hypothesis Syntax

```python
# Config A's metric > Config B's metric
hypothesis="treatment.accuracy > baseline.accuracy"

# Less than
hypothesis="fast.latency < slow.latency"

# Greater than or equal
hypothesis="new.score >= old.score"
```

### Results

```python
results = run(...)

# Raw return values
results.results["config_name"]  # [result1, result2, ...]

# Recorded metrics
results.metrics["config_name"]["metric_name"]  # [val1, val2, ...]

# Hypothesis result (if provided)
results.hypothesis_result.supported  # True/False
results.hypothesis_result.p_value    # Statistical significance

# Save results
results.to_json("results.json")
```

### Live Updates

```python
def on_event(event):
    if event["type"] == "metric":
        print(f"{event['config']}: {event['metric']} = {event['value']}")

results = run(
    fn=my_function,
    configs={...},
    on_event=on_event,
)
```

## Philosophy

1. **No ceremony for exploration** — Just run the function with configs
2. **Same code, more rigor** — Add `hypothesis=` to crystallize, don't rewrite
3. **Hypothesis as pre-registration** — Commit before seeing results
4. **Statistical output built-in** — p-values, effect sizes, not just means

## Install

```bash
# Basic (no statistical tests, just mean comparison)
pip install crystallize-ml

# With statistical tests (scipy)
pip install crystallize-ml[stats]
```

## v0.x Legacy

Looking for the old framework with pipelines, treatments, and plugins? See the [legacy/v0.x branch](https://github.com/brysontang/crystallize/tree/legacy/v0.x).

## License

MIT
