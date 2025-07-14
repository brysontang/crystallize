---
title: Exceptions
---


## <kbd>module</kbd> `crystallize.core.exceptions`






---

## <kbd>class</kbd> `CrystallizeError`
Base class for all Crystallize errors. 





---

## <kbd>class</kbd> `MissingMetricError`
Raised when a required metric is missing from the pipeline's output. 

### <kbd>method</kbd> `MissingMetricError.__init__`

```python
__init__(metric: str) → None
```









---

## <kbd>class</kbd> `PipelineExecutionError`
Raised when a pipeline step fails unexpectedly. 

### <kbd>method</kbd> `PipelineExecutionError.__init__`

```python
__init__(step_name: str, original_exception: Exception) → None
```









