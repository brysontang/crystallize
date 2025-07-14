---
title: Hypothesis
---


## <kbd>module</kbd> `crystallize.core.hypothesis`






---

## <kbd>class</kbd> `Hypothesis`
A quantifiable assertion to verify after experiment execution. 

### <kbd>method</kbd> `Hypothesis.__init__`

```python
__init__(
    verifier: Callable[[Mapping[str, Sequence[Any]], Mapping[str, Sequence[Any]]], Mapping[str, Any]],
    metrics: Optional[str, Sequence[str], Sequence[Sequence[str]]] = None,
    ranker: Optional[Callable[[Mapping[str, Any]], float]] = None,
    name: Optional[str] = None
) → None
```








---

### <kbd>method</kbd> `Hypothesis.rank_treatments`

```python
rank_treatments(verifier_results: Mapping[str, Any]) → Mapping[str, Any]
```





---

### <kbd>method</kbd> `Hypothesis.verify`

```python
verify(
    baseline_metrics: Mapping[str, Sequence[Any]],
    treatment_metrics: Mapping[str, Sequence[Any]]
) → Any
```






