# Crystallize

**From Play to Proof.**

Run experiments. Start exploring, then crystallize your findings with a hypothesis.

```bash
pip install crystallize-ml
```

## Quick Start

### Phase 1: Explore

Just play around. No ceremony.

```python
from crystallize import explore

def play_game(config, ctx):
    # Your logic here
    winner = "treatment" if config["power"] > 5 else "baseline"
    ctx.record("win", 1 if winner == "treatment" else 0)
    return {"winner": winner}

exp = explore(
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
⚠  Exploratory mode (run: exp_a1b2c3d4)
   When ready to prove something: exp.crystallize("a.x > b.x")

Results:
  weak:
    win: [0, 0, 0, 0, 0] → μ=0.00
  strong:
    win: [1, 1, 1, 1, 1] → μ=1.00
```

### Phase 2: Crystallize

You noticed something. Now prove it.

```python
result = exp.crystallize(
    hypothesis="strong.win > weak.win",
    replicates=20,
)
print(result.report())
```

Output:
```
✓ Integrity: VALID

✓ Hypothesis SUPPORTED: strong.win > weak.win
  strong.win (μ=1.00, n=20) > weak.win (μ=0.00, n=20)
  Effect: 1.000, 95% CI [1.000, 1.000]
  p = 0.0002

Proof:
  run_id: conf_e5f6g7h8
  parent: exp_a1b2c3d4
  lineage: lin_xyz123
  prereg: .crystallize/prereg/conf_e5f6g7h8.json
  replicates: 5-24
  fn_sha: abc123def456
  git: 80439f7
  results: .crystallize/runs/conf_e5f6g7h8.json
```

## The API

### explore()

```python
from crystallize import explore

exp = explore(
    fn=my_function,           # fn(config) or fn(config, ctx)
    configs={...},            # {"name": {config_dict}, ...}
    replicates=5,             # How many times per config
    seed=42,                  # For reproducibility
    audit="calls",            # "calls" or "none" (for ctx.http tracking)
    on_event=callback,        # For live UIs
    progress=True,            # Show progress bar
)
```

### exp.crystallize()

```python
result = exp.crystallize(
    hypothesis="a.metric > b.metric",  # What to prove
    replicates=20,                     # Fresh replicates for confirm
    allow_confounds=False,             # Override: allow hidden variables
    allow_no_audit=False,              # Override: allow no ctx.http usage
    allow_fn_change=False,             # Override: allow function change
    seed=42,                           # Seed for confirm run
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

### Audited HTTP Calls

```python
def my_function(config, ctx):
    # Use ctx.http for provenance tracking
    response = ctx.http.post(
        "https://api.example.com/chat",
        json={"model": config["model"], "prompt": "Hello"}
    )
    return response.json()
```

### Hidden Variables

```python
# Check what parameters aren't controlled by config
print(exp.hidden_variables().pretty())
```

Output:
```
Hidden Variables Report
========================================

🔴 [HIGH] temperature
   Value: None
   Source: implicit_default
   Why: 'temperature' (affects model behavior) was not set; API will use default
   Seen in: baseline, treatment

🟡 [MED] system
   Value: "You are a helpful assistant"
   Source: hardcoded
   Why: 'system' (affects model behavior) is hardcoded to 'You are...'
   Seen in: baseline, treatment
```

### Integrity Status

Results include integrity verification:

- **VALID**: All conditions met for a valid experiment
- **CONFOUNDED**: Hidden variables detected
- **REUSED_DATA**: Replicates were not fresh
- **NO_AUDIT**: `ctx.http` not used (unknown provenance)
- **FN_CHANGED**: Function changed between explore and confirm
- **NO_PREREG**: Pre-registration missing

### Results

```python
# Access results
exp.results["config_name"]           # [result1, result2, ...]
exp.metrics["config_name"]["metric"] # [val1, val2, ...]
exp.config_fingerprints["config"]    # SHA256 fingerprint

# After crystallize
result.supported                     # True/False
result.hypothesis_result.p_value     # Statistical significance
result.hypothesis_result.ci          # 95% confidence interval
result.integrity                     # IntegrityStatus
result.report()                      # Formatted report

# Serialization
result.to_dict()                     # Python dict
```

## Philosophy

1. **No ceremony for exploration** — Just run the function with configs
2. **Same code, more rigor** — Add `hypothesis=` to crystallize, don't rewrite
3. **Hypothesis as pre-registration** — Commit before seeing results
4. **Integrity built-in** — Hidden variables, fresh replicates, audit trail

## Install

```bash
# Basic (permutation tests built-in)
pip install crystallize-ml

# With scipy for more statistical tests
pip install crystallize-ml[stats]

# With requests for ctx.http
pip install crystallize-ml[http]
```

## v0.x Legacy

Looking for the old framework with pipelines, treatments, and plugins? See the [legacy/v0.x branch](https://github.com/brysontang/crystallize/tree/legacy/v0.x).

## License

MIT
