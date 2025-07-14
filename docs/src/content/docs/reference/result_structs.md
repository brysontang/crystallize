---
title: Result_structs
---


## <kbd>module</kbd> `crystallize.core.result_structs`






---

## <kbd>class</kbd> `TreatmentMetrics`
TreatmentMetrics(metrics: 'Dict[str, List[Any]]') 

### <kbd>method</kbd> `TreatmentMetrics.__init__`

```python
__init__(metrics: 'Dict[str, List[Any]]') → None
```









---

## <kbd>class</kbd> `HypothesisResult`
HypothesisResult(name: 'str', results: 'Dict[str, Dict[str, Any]]', ranking: 'Dict[str, Any]') 

### <kbd>method</kbd> `HypothesisResult.__init__`

```python
__init__(
    name: 'str',
    results: 'Dict[str, Dict[str, Any]]',
    ranking: 'Dict[str, Any]'
) → None
```








---

### <kbd>method</kbd> `HypothesisResult.get_for_treatment`

```python
get_for_treatment(treatment: 'str') → Optional[Dict[str, Any]]
```






---

## <kbd>class</kbd> `ExperimentMetrics`
ExperimentMetrics(baseline: 'TreatmentMetrics', treatments: 'Dict[str, TreatmentMetrics]', hypotheses: 'List[HypothesisResult]') 

### <kbd>method</kbd> `ExperimentMetrics.__init__`

```python
__init__(
    baseline: 'TreatmentMetrics',
    treatments: 'Dict[str, TreatmentMetrics]',
    hypotheses: 'List[HypothesisResult]'
) → None
```








---

### <kbd>method</kbd> `ExperimentMetrics.to_df`

```python
to_df()
```






