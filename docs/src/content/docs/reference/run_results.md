---
title: Run_results
---


## <kbd>module</kbd> `crystallize.core.run_results`






---

## <kbd>class</kbd> `ReplicateResult`
Holds the complete results from a single replicate execution. 

### <kbd>method</kbd> `ReplicateResult.__init__`

```python
__init__(
    baseline_metrics: Optional[Mapping[str, Any]],
    baseline_seed: Optional[int],
    treatment_metrics: Dict[str, Mapping[str, Any]],
    treatment_seeds: Dict[str, int],
    errors: Dict[str, Exception],
    provenance: Dict[str, List[Mapping[str, Any]]]
) → None
```









