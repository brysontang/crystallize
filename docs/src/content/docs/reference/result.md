---
title: Result
---


## <kbd>module</kbd> `crystallize.core.result`






---

## <kbd>class</kbd> `Result`
Outputs of an experiment run including metrics and provenance. 

### <kbd>method</kbd> `Result.__init__`

```python
__init__(
    metrics: 'ExperimentMetrics',
    artifacts: 'Optional[Dict[str, Any]]' = None,
    errors: 'Optional[Dict[str, Exception]]' = None,
    provenance: 'Optional[Dict[str, Any]]' = None
) → None
```








---

### <kbd>method</kbd> `Result.get_artifact`

```python
get_artifact(name: 'str') → Any
```

Return an artifact by name if it was recorded. 

---

### <kbd>method</kbd> `Result.get_hypothesis`

```python
get_hypothesis(name: 'str') → Optional[HypothesisResult]
```

Return the :class:`HypothesisResult` with ``name`` if present. 

---

### <kbd>method</kbd> `Result.print_tree`

```python
print_tree(fmt: 'str' = 'treatment > replicate > step') → None
```

Print a color-coded tree of execution provenance. The ``fmt`` string controls
the hierarchy and may include ``"treatment"``, ``"replicate"``, ``"step`` and
``"action"``. When ``"action"`` is present as the final token, each step lists
the context reads, writes and metric updates. Uses ``rich`` for color if
installed.


