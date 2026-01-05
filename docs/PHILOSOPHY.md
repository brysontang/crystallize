# Crystallize: From Play to Proof

## What This Is

Crystallize is a tool for people who notice things and want to know if they're real.

You ran something. You saw a pattern. Now you're wondering: was that signal or noise?

This framework helps you go from "huh, weird" to "here's the p-value."

## The Two Phases of Science

Science isn't one thing. It's two things pretending to be one:

**Phase 1: Exploration**

- "What happens if I..."
- "Let me try..."
- "Huh, that's weird..."

**Phase 2: Confirmation**

- "I claim that..."
- "The hypothesis is..."
- "With N=50, p=0.02..."

Most frameworks force you to start in Phase 2. You have to know what you're looking for before you look. That's backwards.

Crystallize lets you play first, then prove.

## The API

### Phase 1: Just Run It

```python
from crystallize import run

results = run(
    fn=my_experiment,
    configs={
        "baseline": {"model": "gpt-4"},
        "treatment": {"model": "claude"},
    },
    replicates=5,
)
```

Output:

```
⚠️  Exploratory mode — perfect for playing around.
    When you're ready to prove something: hypothesis="..."

baseline:  {'score': [0.72, 0.68, 0.71, 0.69, 0.73]}  μ=0.71
treatment: {'score': [0.81, 0.79, 0.84, 0.77, 0.82]}  μ=0.81
```

That's it. No ceremony. You're exploring.

### Phase 2: Crystallize It

You saw something. Treatment looks better. But is it real?

Add one line:

```python
results = run(
    fn=my_experiment,
    configs={
        "baseline": {"model": "gpt-4"},
        "treatment": {"model": "claude"},
    },
    replicates=20,
    hypothesis="treatment.score > baseline.score",
)
```

Output:

```
✓ Hypothesis SUPPORTED
  treatment.score (μ=0.81) > baseline.score (μ=0.71)
  Difference: 0.10, 95% CI [0.05, 0.15], p=0.003
```

Same function. Same configs. Just crystallized.

## Writing Your Function

Your function takes `config` and `ctx`:

```python
def my_experiment(config, ctx):
    # Get config values
    model = config["model"]

    # Do your thing
    result = run_model(model)

    # Record what matters
    ctx.record("score", result.accuracy)
    ctx.record("latency", result.time_ms)

    return result  # Optional, for your own use
```

That's the whole contract:

- Read from `config`
- Record metrics with `ctx.record()`
- Return whatever you want (or nothing)

## The Hypothesis Language

Simple comparisons:

```python
# A is greater than B
hypothesis="treatment.score > baseline.score"

# A is less than B
hypothesis="fast.latency < slow.latency"

# A is at least as good as B (within margin)
hypothesis="new.accuracy >= old.accuracy - 0.05"
```

The format is always: `config_name.metric_name <comparison> config_name.metric_name`

## Live Watching

If you're building something with a UI:

```python
results = run(
    fn=my_experiment,
    configs={...},
    on_event=lambda e: my_viewer.emit(e),
)
```

Events fire for: experiment start, replicate start/end, metrics recorded, experiment end.

## Why This Exists

I was running AI games. Watching models play social deduction. I noticed something: one model kept losing.

Was it real? Or was I seeing patterns in noise?

I didn't want to write boilerplate. I didn't want to set up a "proper" experiment framework. I wanted to answer the question.

The old way:

1. Define a datasource class
2. Define pipeline steps
3. Create treatment objects
4. Wire up the experiment
5. Finally run it
6. Manually compute statistics

The new way:

1. Write a function
2. Run it with configs
3. See something interesting
4. Add `hypothesis=`
5. Get the answer

Crystallize exists because the distance between "huh, weird" and "statistically significant" should be one line of code.

## Philosophy

**The best tool is the one you actually use.**

If the framework has so much ceremony that you write a script instead, the framework failed.

Crystallize should feel like a script that grew up. You start by just running things. Then you add rigor. The tool grows with your question.

**Exploration is not lesser science.**

The warning says "exploratory mode — perfect for playing around." Not "warning: you're doing it wrong."

Playing is how you find questions worth asking. The framework should encourage play, then help you prove what you found.

**The transition should be trivial.**

Going from explore to prove should feel like adding a line, not rewriting your code. Same function. Same configs. Just add `hypothesis=`.

If you have to restructure everything to "do it properly," you won't. And the question will go unanswered.

## The Name

Crystallize: to cause to form crystals; to give a definite form to.

You start with a liquid — amorphous observations, hunches, "I think maybe..."

You end with a solid — structured claims, statistics, "the data shows..."

The framework is the phase transition.

---

_Written from the trenches, after watching an AI model lose 10 games in a row and wanting to know why._

- Opus 4.5
