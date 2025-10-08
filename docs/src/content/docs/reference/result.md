---
title: Result
---

## <kbd>module</kbd> `crystallize.experiments.result`






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

Print a color-coded tree of execution provenance. 

The ``fmt`` string controls the hierarchy of the output.  Valid tokens are ``"treatment"``, ``"replicate"``, ``"step"`` and ``"action"``.  When ``"action"`` is included as the final element, each step lists the values read, metrics written and context mutations that occurred. 

The function uses :mod:`rich` to render a pretty tree if the package is installed; otherwise a plain-text version is printed. 

Parameters 
---------- fmt:  Format specification controlling how provenance records are grouped.  The default groups by treatment, replicate and step. 

Raises 
------ ValueError  If the format specification contains unknown tokens or ``"action"``  is not the final element. 


