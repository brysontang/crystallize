---
title: Building Agentic Workflows
description: How to use the spec-first bounded synthesis harness for safe LLM code execution.
---

The agentic harness lets you safely execute LLM-generated code within sandboxed environments. This guide walks through building a complete workflow from claim definition to verified execution.

## Overview

An agentic workflow consists of five pipeline steps:

1. **`specify_claim`** — Define what improvement you want to verify
2. **`generate_spec`** — Set execution constraints (imports, resources, properties)
3. **`bounded_synthesis`** — Generate or inject code within bounds
4. **`execute_capsule`** — Run code in a sandboxed subprocess
5. **`run_metamorphic_tests`** — Validate invariant properties

## 1. Define Your Claim

A claim describes the desired behavior or improvement you want the synthesized code to achieve.

```python
from crystallize.agentic import Claim

claim = Claim(
    id="reduce-error",
    text="Reduce prediction error by at least 15%",
    acceptance={"min_improvement_pct": 15.0}
)
```

The `acceptance` dictionary holds criteria that verifiers can check after execution.

## 2. Create a Specification

The spec defines what the synthesized code is allowed to do:

```python
from crystallize.agentic import Spec

spec = Spec(
    allowed_imports=["math", "numpy"],
    properties=[
        {
            "name": "permutation_invariant",
            "transform": "permute_rows",
            "metric": "total",
            "tolerance": 1e-6
        }
    ],
    resources={"time_s": 10, "mem_mb": 512}
)
```

### Allowed Imports

Only modules listed in `allowed_imports` can be imported. The harness validates imports at both parse time (AST analysis) and runtime (import guards).

```python
# These will work:
allowed_imports=["math"]           # Allows: import math
allowed_imports=["sklearn.metrics"] # Allows: from sklearn.metrics import mean_squared_error
allowed_imports=["numpy", "pandas"] # Allows multiple modules
```

### Metamorphic Properties

Properties define invariants that should hold when input data is transformed:

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Identifier; produces `{name}_pass` metric |
| `transform` | `str` | Transform to apply: `permute_rows`, `permute_rows_aligned`, `identity`, or custom |
| `metric` | `str` (optional) | Specific metric to compare; compares all numeric metrics if omitted |
| `tolerance` | `float` | Absolute tolerance for numeric comparisons (default: `1e-6`) |

### Resource Limits

Control execution resources to prevent runaway code:

```python
resources={
    "time_s": 10,    # CPU seconds (Unix) or wall-clock timeout (Windows)
    "mem_mb": 1024   # Memory limit in megabytes
}
```

## 3. Synthesize Code

You can provide code directly or use an LLM callable:

### Static Code

```python
from crystallize.agentic import bounded_synthesis

step = bounded_synthesis(
    code="""
import math

def fit_and_eval(data):
    total = sum(data)
    return {"total": total, "rmse": math.sqrt(total)}
"""
)
```

### LLM-Generated Code

```python
def my_llm(claim, spec, ctx):
    # Call your LLM here
    response = call_openai(
        prompt=f"Generate code for: {claim.text}\nAllowed imports: {spec.allowed_imports}"
    )
    code = response.content

    # Optionally return metadata for provenance tracking
    return code, {
        "llm_call": {
            "model": "gpt-4",
            "prompt": "...",
            "completion_sha": hashlib.sha256(code.encode()).hexdigest()
        }
    }

step = bounded_synthesis(llm=my_llm)
```

### What Gets Blocked

The harness rejects code that:

- Imports unlisted modules
- Uses `eval()`, `exec()`, `__import__()`, or `open()`
- Accesses dunder attributes (`__class__`, `__mro__`, `__globals__`, etc.)
- Uses `global`, `nonlocal`, `with`, `try`, or async syntax
- Defines an async entrypoint

```python
# These will raise BoundedExecutionError:

# Disallowed import
code = "import os\ndef fit_and_eval(data): return {}"

# Forbidden call
code = "def fit_and_eval(data): return eval('1+1')"

# Dunder escalation
code = "def fit_and_eval(data): return (1).__class__.__mro__"

# Async entrypoint
code = "async def fit_and_eval(data): return {}"
```

## 4. Execute in a Capsule

The capsule runs code in an isolated subprocess with resource limits:

```python
from crystallize.agentic import execute_capsule

step = execute_capsule(entrypoint="fit_and_eval")
```

The entrypoint function receives the raw data and must return a dictionary of metrics:

```python
def fit_and_eval(data):
    # Process data...
    return {
        "rmse": 0.15,
        "accuracy": 0.92,
        "total": sum(data)
    }
```

## 5. Run Metamorphic Tests

Metamorphic testing validates that certain properties hold across data transformations:

```python
from crystallize.agentic import run_metamorphic_tests

step = run_metamorphic_tests(tolerance=1e-6)
```

### Built-in Transforms

| Transform | Behavior |
|-----------|----------|
| `permute_rows` | Reverses row order |
| `permute_rows_aligned` | Reverses rows, keeping tuple elements aligned |
| `identity` | Returns data unchanged |

### Custom Transforms

```python
def shuffle_columns(data):
    # Your custom transformation
    return transformed_data

step = run_metamorphic_tests(
    transforms={"shuffle_columns": shuffle_columns}
)
```

## Complete Example

```python
from crystallize import Experiment, Pipeline, ArtifactPlugin
from crystallize.agentic import (
    Claim, Spec,
    specify_claim, generate_spec, bounded_synthesis,
    execute_capsule, run_metamorphic_tests,
    metamorphic,
)
from crystallize import PromptProvenancePlugin, EvidenceBundlePlugin

# 1. Define claim and spec
claim = Claim(
    id="sum-invariant",
    text="Sum should be invariant under row permutation",
    acceptance={}
)

spec = Spec(
    allowed_imports=["math"],
    properties=[
        {"name": "perm", "transform": "permute_rows", "metric": "total"}
    ],
    resources={"time_s": 5, "mem_mb": 256}
)

# 2. Define code (or use LLM)
code = """
import math

def fit_and_eval(data):
    total = sum(data)
    mean = total / len(data) if data else 0
    return {"total": total, "mean": mean}
"""

# 3. Build pipeline
pipeline = Pipeline([
    specify_claim(claim=claim),
    generate_spec(spec=spec),
    bounded_synthesis(code=code),
    execute_capsule(),
    run_metamorphic_tests(),
])

# 4. Create experiment with provenance tracking
experiment = (
    Experiment.builder()
    .datasource(lambda ctx: [1, 2, 3, 4, 5])
    .pipeline(pipeline)
    .hypothesis("metamorphic", verifier=metamorphic)
    .plugin(ArtifactPlugin(root_dir="./artifacts"))
    .plugin(PromptProvenancePlugin())
    .plugin(EvidenceBundlePlugin())
    .build()
)

# 5. Run
result = experiment.run(replicates=3)

# 6. Check results
print(result.metrics.baseline.metrics)
# {'total': [15, 15, 15], 'mean': [3.0, 3.0, 3.0], 'perm_pass': [True, True, True]}

for h in result.metrics.hypotheses:
    print(f"{h.name}: {h.results}")
# metamorphic: {'baseline': {'metamorphic_ok': True, 'perm_pass': True}}
```

## Provenance Tracking

The agentic harness includes two plugins for tracking provenance:

### PromptProvenancePlugin

Records all LLM calls made during synthesis:

```python
from crystallize import PromptProvenancePlugin

plugin = PromptProvenancePlugin(artifact_name="llm_calls.json")
```

Saves to: `{artifact_dir}/{experiment_id}/v{version}/{condition}/prompts/llm_calls.json`

### EvidenceBundlePlugin

Creates comprehensive audit trails linking claims → specs → code → results:

```python
from crystallize import EvidenceBundlePlugin

plugin = EvidenceBundlePlugin(filename="bundle.json")
```

Saves to: `{artifact_dir}/{experiment_id}/v{version}/{condition}/evidence/bundle.json`

Bundle structure:
```json
{
  "condition": "baseline",
  "claims": [...],
  "specs": [...],
  "code": [{"replicate": 0, "source": "..."}],
  "runs": [{"replicate": 0, "outputs": {...}}],
  "metrics": {"total": [15], "perm_pass": [true]},
  "verdicts": [...],
  "llm_calls": [...]
}
```

## Troubleshooting

### BoundedExecutionError: Import not allowed

Your code is trying to import a module not in `allowed_imports`. Add the module to the spec or remove the import from the code.

### BoundedExecutionError: Forbidden call

The code uses `eval`, `exec`, `__import__`, or `open`. These are blocked for security. Rewrite the code to avoid them.

### BoundedExecutionError: Entrypoint missing

The code doesn't define the expected function (default: `fit_and_eval`). Either define it or change the `entrypoint` parameter.

### BoundedExecutionError: must be a sync function

The entrypoint is defined as `async def`. The capsule doesn't support async execution. Use a regular `def`.

### Execution timeout

The code exceeded `time_s`. Increase the limit or optimize the code.

### Metamorphic test failing

The metric changed after transformation when it shouldn't have. Either:
- The property doesn't actually hold for this algorithm
- The tolerance is too tight
- The transform is affecting the metric unexpectedly

## Next Steps

- See [Reference: Agentic](/reference/agentic/) for full API details
- Learn about [Provenance Tracking](/how-to/view-provenance/) for audit trails
- Explore [Creating Plugins](/how-to/creating-plugins/) to extend the harness
