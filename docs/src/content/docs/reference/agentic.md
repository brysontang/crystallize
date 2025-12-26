---
title: Agentic Harness
description: API reference for the spec-first bounded synthesis harness.
---

The `crystallize.agentic` module provides a spec-first bounded synthesis harness built on top of the core Crystallize APIs. It enables safe execution of LLM-generated code within sandboxed environments, with metamorphic testing for validation.

## <kbd>module</kbd> `crystallize.agentic.schema`

### <kbd>class</kbd> `Claim`

A frozen dataclass representing a desired improvement or behavior to verify.

```python
from crystallize.agentic import Claim

claim = Claim(
    id="improve-rmse",
    text="Reduce RMSE by at least 10% compared to baseline",
    acceptance={"min_improvement": 10.0}
)
```

**Attributes:**

- **`id`** (`str`): Unique identifier for the claim.
- **`text`** (`str`): Human-readable description of the desired behavior.
- **`acceptance`** (`Dict[str, Any]`): Criteria for accepting the claim as met.

---

### <kbd>class</kbd> `Spec`

A frozen dataclass defining execution constraints for bounded synthesis.

```python
from crystallize.agentic import Spec

spec = Spec(
    allowed_imports=["math", "numpy", "sklearn.metrics"],
    properties=[
        {"name": "permutation_invariant", "transform": "permute_rows", "metric": "total"}
    ],
    contracts=[],
    resources={"time_s": 10, "mem_mb": 512}
)
```

**Attributes:**

- **`allowed_imports`** (`List[str]`): Modules the synthesized code may import. Attempts to import unlisted modules raise `BoundedExecutionError`.
- **`properties`** (`List[Dict[str, Any]]`): Metamorphic properties to validate. Each entry specifies a `name`, `transform` (or `metamorphic`), optional `metric`, and `tolerance`.
- **`contracts`** (`List[str]`): Reserved for future contract specifications.
- **`resources`** (`Dict[str, int]`): Execution limits. Keys: `time_s` (CPU seconds), `mem_mb` (memory in MB). Defaults: `{"time_s": 10, "mem_mb": 1024}`.

---

## <kbd>module</kbd> `crystallize.agentic.steps`

Pipeline steps composing the bounded synthesis workflow.

---

### <kbd>class</kbd> `BoundedExecutionError`

Exception raised when bounded synthesis or capsule execution fails validation.

```python
from crystallize.agentic import BoundedExecutionError

# Raised when:
# - Code imports a disallowed module
# - Code uses forbidden syntax (eval, exec, __import__, etc.)
# - Code attempts dunder attribute escalation (__class__, __mro__, etc.)
# - Entrypoint function is missing or async
# - Capsule execution times out or exceeds memory limits
# - Runtime module loading violates the allowlist
```

---

### <kbd>function</kbd> `specify_claim`

```python
@pipeline_step()
def specify_claim(
    data: Any,
    ctx: FrozenContext,
    *,
    claim: Claim | Mapping[str, Any],
) -> Tuple[Tuple[Claim, Any], Dict[str, Any]]
```

Inject a claim into the pipeline context.

**Parameters:**

- **`data`**: Input data to pass through.
- **`ctx`**: The frozen execution context.
- **`claim`**: A `Claim` instance or dict with keys `id`, `text`, `acceptance`.

**Returns:**

- Tuple of `(Claim, data)` and metadata dict containing `claim_id`.

**Context writes:** `claim`, `raw_data`

---

### <kbd>function</kbd> `generate_spec`

```python
@pipeline_step()
def generate_spec(
    data: Tuple[Claim, Any],
    ctx: FrozenContext,
    *,
    llm: Optional[Callable[[Claim, Any, FrozenContext], Any]] = None,
    spec: Optional[Spec | Mapping[str, Any]] = None,
) -> Tuple[Tuple[Claim, Spec, Any], Dict[str, Any]]
```

Generate or accept a specification for bounded synthesis.

**Parameters:**

- **`data`**: Tuple of `(Claim, raw_data)` from `specify_claim`.
- **`ctx`**: The frozen execution context.
- **`llm`**: Optional callable that generates a spec via LLM. Receives `(claim, data, ctx)` and returns a `Spec` or `(Spec, metadata)` tuple.
- **`spec`**: Static spec to use instead of LLM generation.

**Returns:**

- Tuple of `(Claim, Spec, raw_data)` and metadata dict containing `spec_json`.

**Context writes:** `spec`

**Raises:** `ValueError` if neither `llm` nor `spec` is provided.

---

### <kbd>function</kbd> `bounded_synthesis`

```python
@pipeline_step()
def bounded_synthesis(
    data: Tuple[Claim, Spec, Any],
    ctx: FrozenContext,
    *,
    llm: Optional[Callable[[Claim, Spec, FrozenContext], Any]] = None,
    code: Optional[str] = None,
    entrypoint: str = "fit_and_eval",
) -> Tuple[Tuple[Claim, Spec, str, Any], Dict[str, Any]]
```

Synthesize code within the bounds defined by the spec.

The generated code is validated via AST analysis before execution:
- Only imports listed in `spec.allowed_imports` are permitted
- Dangerous calls (`eval`, `exec`, `__import__`, `open`) are blocked
- Dunder attribute access (`__class__`, `__mro__`, `__globals__`, etc.) is forbidden
- Forbidden syntax (`global`, `nonlocal`, `with`, `try`, async constructs) is rejected
- The entrypoint function must exist and be synchronous

**Parameters:**

- **`data`**: Tuple of `(Claim, Spec, raw_data)` from `generate_spec`.
- **`ctx`**: The frozen execution context.
- **`llm`**: Optional callable for LLM-based code generation.
- **`code`**: Static code string to use instead of LLM.
- **`entrypoint`**: Name of the function to call. Default: `"fit_and_eval"`.

**Returns:**

- Tuple of `(Claim, Spec, code_str, raw_data)` and metadata dict containing `code_sha`.

**Context writes:** `generated_code`

**Raises:**
- `ValueError` if neither `llm` nor `code` is provided.
- `BoundedExecutionError` if code fails validation.

---

### <kbd>function</kbd> `execute_capsule`

```python
@pipeline_step()
def execute_capsule(
    data: Tuple[Claim, Spec, str, Any],
    ctx: FrozenContext,
    *,
    entrypoint: str = "fit_and_eval",
) -> Tuple[Tuple[Claim, Spec, Dict[str, Any]], Dict[str, Any]]
```

Execute synthesized code in a sandboxed subprocess.

The capsule enforces:
- CPU time limits via `setrlimit` (Unix) or wall-clock timeout (Windows)
- Memory limits via `setrlimit`
- File size limits
- Import guards at runtime
- Module diffing to detect unauthorized imports

**Parameters:**

- **`data`**: Tuple of `(Claim, Spec, code_str, raw_data)` from `bounded_synthesis`.
- **`ctx`**: The frozen execution context.
- **`entrypoint`**: Function to invoke with the raw data.

**Returns:**

- Tuple of `(Claim, Spec, metrics_dict)` and metadata containing numeric metrics.

**Context writes:** `capsule_output`

**Raises:** `BoundedExecutionError` if execution fails, times out, or returns non-mapping.

---

### <kbd>function</kbd> `run_metamorphic_tests`

```python
@pipeline_step()
def run_metamorphic_tests(
    data: Tuple[Claim, Spec, Dict[str, Any]],
    ctx: FrozenContext,
    *,
    entrypoint: str = "fit_and_eval",
    transforms: Optional[Mapping[str, Callable[[Any], Any]]] = None,
    tolerance: float = 1e-6,
) -> Tuple[Tuple[Claim, Spec, Dict[str, Any]], Dict[str, Any]]
```

Validate metamorphic properties defined in the spec.

For each property in `spec.properties`, applies the specified transform to the input data, re-executes the code, and compares metrics against the baseline.

**Built-in transforms:**

- `permute_rows`: Reverses the order of rows/elements
- `permute_rows_aligned`: Reverses rows while keeping tuple elements aligned
- `identity`: Returns data unchanged (useful for custom transform injection)

**Parameters:**

- **`data`**: Tuple of `(Claim, Spec, base_metrics)` from `execute_capsule`.
- **`ctx`**: The frozen execution context.
- **`entrypoint`**: Function to invoke for transformed execution.
- **`transforms`**: Custom transform functions keyed by name.
- **`tolerance`**: Default tolerance for numeric comparisons.

**Returns:**

- Original data tuple and metadata containing `{property_name}_pass: bool` for each property.

**Context writes:** `metamorphic_{name}_result` for each property.

**Raises:** `BoundedExecutionError` if required context is missing or transform execution fails.

---

### <kbd>function</kbd> `record_llm_call`

```python
def record_llm_call(
    ctx: FrozenContext,
    call: Mapping[str, Any],
    *,
    prefix: str = "llm_call",
) -> str
```

Persist metadata about an LLM invocation in the context.

**Parameters:**

- **`ctx`**: The frozen execution context.
- **`call`**: Dictionary of LLM call metadata (model, prompt, response, etc.).
- **`prefix`**: Key prefix for the context entry.

**Returns:** The generated context key (e.g., `llm_call_a1b2c3d4...`).

---

## <kbd>module</kbd> `crystallize.agentic.verifiers`

Verifier functions for hypothesis testing on bounded synthesis outputs.

---

### <kbd>function</kbd> `metamorphic`

```python
@verifier
def metamorphic(
    baseline_samples: Mapping[str, Sequence[Any]],
    treatment_samples: Mapping[str, Sequence[Any]],
    *,
    tolerance: float = 1e-6,
) -> Dict[str, Any]
```

Verify that all metamorphic properties passed.

**Parameters:**

- **`baseline_samples`**: Baseline metrics (unused, for API compatibility).
- **`treatment_samples`**: Treatment metrics containing `{name}_pass` keys.
- **`tolerance`**: Unused (properties define their own tolerances).

**Returns:**

```python
{
    "metamorphic_ok": bool,  # True if all properties passed
    "{name}_pass": bool,     # Per-property results
    ...
}
```

---

### <kbd>function</kbd> `meets_claim`

```python
@verifier
def meets_claim(
    baseline_samples: Mapping[str, Sequence[Any]],
    treatment_samples: Mapping[str, Sequence[Any]],
    *,
    min_pct: float = 5.0,
) -> Dict[str, Any]
```

Check whether treatment RMSE improves over baseline by at least `min_pct`.

**Note:** The `p_value` returned is a simplified heuristic (inverse of improvement percentage), not a formal statistical test. For rigorous hypothesis testing, consider using `scipy.stats.ttest_ind` or similar.

**Parameters:**

- **`baseline_samples`**: Must contain `rmse` key with numeric values.
- **`treatment_samples`**: Must contain `rmse` key with numeric values.
- **`min_pct`**: Minimum percentage improvement required.

**Returns:**

```python
{
    "pct_improvement": float,  # Percentage improvement
    "meets_claim": bool,       # True if improvement >= min_pct
    "p_value": float,          # Heuristic p-value (not a statistical test)
}
```

---

## Complete Workflow Example

```python
from crystallize import Experiment, Pipeline, FrozenContext
from crystallize.agentic import (
    Claim, Spec,
    specify_claim, generate_spec, bounded_synthesis,
    execute_capsule, run_metamorphic_tests,
    metamorphic,
)
from crystallize import PromptProvenancePlugin, EvidenceBundlePlugin, ArtifactPlugin

# Define the claim
claim = Claim(
    id="sum-invariant",
    text="Sum should be invariant to row permutation",
    acceptance={}
)

# Define the spec
spec = Spec(
    allowed_imports=[],
    properties=[{"name": "perm", "transform": "permute_rows", "metric": "total"}],
    resources={"time_s": 5, "mem_mb": 256}
)

# Define the code (in practice, this would come from an LLM)
code = """
def fit_and_eval(data):
    return {"total": sum(data)}
"""

# Build the pipeline
pipeline = Pipeline([
    specify_claim(claim=claim),
    generate_spec(spec=spec),
    bounded_synthesis(code=code),
    execute_capsule(),
    run_metamorphic_tests(),
])

# Run the experiment
experiment = (
    Experiment.builder()
    .datasource(lambda ctx: [1, 2, 3, 4, 5])
    .pipeline(pipeline)
    .hypothesis("metamorphic_check", verifier=metamorphic)
    .plugin(ArtifactPlugin())
    .plugin(PromptProvenancePlugin())
    .plugin(EvidenceBundlePlugin())
    .build()
)

result = experiment.run(replicates=1)
print(result.metrics.baseline.metrics)
# {'total': [15], 'perm_pass': [True]}
```

---

## Security Model

The agentic harness implements defense-in-depth:

1. **AST Validation** (parse time):
   - Import allowlisting
   - Forbidden call detection (`eval`, `exec`, `__import__`, `open`)
   - Dunder attribute blocking
   - Syntax restrictions

2. **Runtime Guards** (execution time):
   - Custom `__builtins__` with safe subset
   - Import function replacement
   - Module loading interception

3. **Resource Limits**:
   - CPU time via `setrlimit` (Unix)
   - Memory via `setrlimit` (Unix)
   - File size limits
   - Wall-clock timeout fallback (Windows)

4. **Post-Execution Verification**:
   - Module diff detection
   - Metamorphic property validation
