# Crystallize

**From Play to Proof.**

The distance between "huh, that's weird" and "statistically significant" should be one line of code.

```bash
pip install crystallize-ml --pre
```

## The Story

I was running AI social deduction games — models playing Werewolf against each other. After a dozen rounds, I noticed Claude kept winning as the werewolf. Was that real, or was I pattern-matching on noise?

I didn't want to set up a "proper" experiment framework. I wanted to answer the question.

```python
from crystallize import explore

def play_werewolf(config, ctx):
    game = WerewolfGame(werewolf=config["model"], rounds=config["rounds"])
    result = game.play()
    ctx.record("wins", result.wins)
    ctx.record("survival_rate", result.survived / result.total)
    return result

# Phase 1: Just play around
exp = explore(
    fn=play_werewolf,
    configs={
        "gpt4": {"model": "gpt-4", "rounds": 3},
        "claude": {"model": "claude-3.5-sonnet", "rounds": 3},
    },
    replicates=5,
)
```

```
⚠  Exploratory mode (run: exp_a1b2c3d4)
   When ready to prove something: exp.crystallize("a.x > b.x")

Results:
  gpt4:
    wins: [1, 2, 1, 0, 2] → μ=1.20
    survival_rate: [0.33, 0.67, 0.33, 0.00, 0.67] → μ=0.40
  claude:
    wins: [3, 2, 3, 3, 2] → μ=2.60
    survival_rate: [1.00, 0.67, 1.00, 1.00, 0.67] → μ=0.87
```

Interesting. Claude looks better. But 5 runs isn't proof — that's a hunch.

```python
# Phase 2: Crystallize it
result = exp.crystallize(
    hypothesis="claude.wins > gpt4.wins",
    replicates=30,
)
print(result.report())
```

```
✓ Integrity: VALID

✓ Hypothesis SUPPORTED: claude.wins > gpt4.wins
  claude.wins (μ=2.47, n=30) > gpt4.wins (μ=1.13, n=30)
  Effect: 1.333, 95% CI [0.821, 1.845]
  p = 0.0003

Proof:
  run_id: conf_e5f6g7h8
  parent: exp_a1b2c3d4
  prereg: .crystallize/prereg/conf_e5f6g7h8.json
  fn_sha: abc123def456
  git: 80439f7
```

Same function. Same configs. The hunch became a finding.

## How It Works

**Write a function. Run it with configs. See something interesting. Add one line.**

```python
def my_experiment(config, ctx):
    result = do_something(config)
    ctx.record("accuracy", result.accuracy)
    ctx.record("latency", result.latency)
    return result

# Explore — no ceremony
exp = explore(fn=my_experiment, configs={...}, replicates=5)

# Crystallize — prove it
result = exp.crystallize("treatment.accuracy > baseline.accuracy", replicates=30)
```

That's the whole API. Two calls.

### Working with Results

```python
result.supported              # True/False
result.hypothesis_result      # Effect size, CI, p-value
result.integrity              # VALID, CONFOUNDED, REUSED_DATA, ...
result.report()               # Formatted summary (what you saw above)
result.to_dict()              # Serialize everything
```

### What You Get for Free

**Integrity checking** — Crystallize tracks whether your experiment is actually valid:
- Fresh replicates (no reusing exploration data as proof)
- Function fingerprinting (did the code change between explore and confirm?)
- Pre-registration (hypothesis is locked before the confirm run starts)

**Hidden variable detection** — Using `ctx.http` for API calls? Crystallize spots parameters you forgot to control:

```python
print(exp.hidden_variables().pretty())
```
```
🔴 [HIGH] temperature
   Value: None — API will use default
   Seen in: baseline, treatment

🟡 [MED] system
   Value: "You are a helpful assistant" — hardcoded
   Seen in: baseline, treatment
```

**Statistics** — Permutation tests built-in (zero dependencies). Add `scipy` for more.

## Install

```bash
pip install crystallize-ml --pre              # Core (permutation tests built-in)
pip install "crystallize-ml[stats]" --pre     # + scipy for more tests
pip install "crystallize-ml[http]" --pre      # + requests for ctx.http auditing
```

## Philosophy

1. **No ceremony for exploration** — Just run the function with configs
2. **Same code, more rigor** — Crystallize, don't rewrite
3. **Integrity built-in** — Hidden variables, fresh replicates, audit trail
4. **The best framework is the one you actually use** — If it has so much ceremony that you write a script instead, it failed

## License

MIT
