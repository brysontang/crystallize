---
title: Hypothesis
---


## <kbd>module</kbd> `crystallize.core.hypothesis`






---

## <kbd>class</kbd> `Hypothesis`
Encapsulate a statistical test to compare baseline and treatment results. 

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

Rank treatments using the ``ranker`` score function. 

---

### <kbd>method</kbd> `Hypothesis.verify`

```python
verify(
    baseline_metrics: Mapping[str, Sequence[Any]],
    treatment_metrics: Mapping[str, Sequence[Any]]
) → Any
```

Evaluate the hypothesis using selected metric groups. 



**Args:**
 
 - <b>`baseline_metrics`</b>:  Aggregated metrics from baseline runs. 
 - <b>`treatment_metrics`</b>:  Aggregated metrics from a treatment. 



**Returns:**
 The output of the ``verifier`` callable. When multiple metric groups are specified the result is a list of outputs in the same order. 


