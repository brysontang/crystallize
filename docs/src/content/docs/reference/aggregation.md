---
title: Aggregation
---

## <kbd>module</kbd> `crystallize.experiments.aggregation`




**Global Variables**
---------------
- **BASELINE_CONDITION**


---

## <kbd>class</kbd> `ResultAggregator`
Helper for aggregating replicate outputs into a ``Result``. 

### <kbd>method</kbd> `ResultAggregator.__init__`

```python
__init__(pipeline: 'Pipeline', replicates: 'int') → None
```








---

### <kbd>method</kbd> `ResultAggregator.aggregate_results`

```python
aggregate_results(results_list: 'List[ReplicateResult]') → AggregateData
```





---

### <kbd>method</kbd> `ResultAggregator.build_result`

```python
build_result(metrics: 'ExperimentMetrics', aggregate: 'AggregateData') → Result
```






