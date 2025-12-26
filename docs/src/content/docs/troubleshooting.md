---
title: Troubleshooting
description: Common errors after upgrading to v0.25.2 and how to fix them.
---

## TypeError: inject_from_ctx... is not found in the Context

**Cause:** A step asks for a parameter that is not provided via treatments, datasource, or defaults.

**Solution:** Add the value to `config.yaml` or set a default in the step signature.

```yaml
treatments:
  tuned:
    factor: 1.1
```

```python
@pipeline_step()
def scale(data, ctx: FrozenContext, factor: float = 1.0):
    return [x * factor for x in data]
```

## RuntimeError: An asyncio event loop is already running

**Cause:** Calling `exp.run()` inside Jupyter/async environments.

**Solution:** Use the async entrypoint:

```python
import asyncio

if asyncio.get_running_loop():
    result = await exp.arun()
else:
    result = exp.run()
```

## Warning: Using SeedPlugin with executor_type='thread' is not reproducible

**Cause:** Thread pools share RNG state; seeds can interleave across threads.

**Solution:** Prefer processes for reproducible runs:

```python
plugins=[SeedPlugin(), ParallelExecution(executor_type="process")]
```

## ImportError: No module named 'crystallize_extras...'

**Cause:** Extras plugins/steps are referenced but the package is not installed.

**Solution:** Install the extras bundle (or a specific extra):

```bash
pip install --upgrade --pre crystallize-extras[all]
```
