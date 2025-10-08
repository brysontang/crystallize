---
title: Result Structs
---

## <kbd>module</kbd> `crystallize.experiments.result_structs`




**Global Variables**
---------------
- **pd**


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






---

## <kbd>class</kbd> `AggregateData`
Grouped results collected from all replicates. 

### <kbd>method</kbd> `AggregateData.__init__`

```python
__init__(
    baseline_metrics: 'Dict[str, List[Any]]',
    treatment_metrics_dict: 'Dict[str, Dict[str, List[Any]]]',
    baseline_seeds: 'List[int]',
    treatment_seeds_agg: 'Dict[str, List[int]]',
    provenance_runs: "'DefaultDict[str, Dict[int, List[Mapping[str, Any]]]]'",
    errors: 'Dict[str, Exception]'
) → None
```









