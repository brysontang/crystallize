---
title: Migrating to v0.25.2
description: Notes for upgrading existing experiments to the strict injection and deterministic seeding changes.
---

Crystallize v0.25.2 tightens reproducibility and injection rules. Use this guide to adapt existing experiments.

## Strict Parameter Injection (Breaking Change)

- **Old behaviour:** Missing parameters in step signatures were silently filled with `None` or ignored.
- **New behaviour:** Missing required parameters raise `TypeError` at runtime.

**Fix:** Ensure every required parameter is supplied by `config.yaml` or has a default in Python.

```python
# Before: crashes if 'factor' is not in the context/config
@pipeline_step()
def scale(data, ctx: FrozenContext, factor: float) -> list[float]:
    return [x * factor for x in data]

# After: provide a default or add 'factor' to config.yaml treatments
@pipeline_step()
def scale(data, ctx: FrozenContext, factor: float = 1.0) -> list[float]:
    return [x * factor for x in data]
```

In YAML, add missing params under `treatments` or the datasource configuration:

```yaml
treatments:
  tuned:
    factor: 1.2
```

## Deterministic Seeding

Seeding now uses `(master_seed + replicate_id * 31337) % 2**32` instead of Python's `hash()`. Seeds are stable across OSs and between serial/process execution.

- **Impact:** Numerical results may differ from v0.25.1 if you relied on the old hash-based seeds.
- **Action:** Rerun key experiments to refresh baselines; no code changes required.

## CLI Updates

- Threaded execution is flagged as non-reproducible when `SeedPlugin` is active; use `executor_type="process"` for deterministic runs.
- The CLI includes an **LLM Data** tab with XML summaries for downstream analysis.
