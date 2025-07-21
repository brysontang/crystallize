---
title: Datasource
---


## <kbd>module</kbd> `crystallize.core.datasource`






---

## <kbd>class</kbd> `DataSource`
Abstract provider of input data for an experiment. 




---

### <kbd>method</kbd> `DataSource.fetch`

```python
fetch(ctx: crystallize.core.context.FrozenContext) → Any
```

Return raw data for a single pipeline run. 

Implementations may load data from disk, generate synthetic samples or access remote sources.  They should be deterministic with respect to the provided context. 



**Args:**
 
 - <b>`ctx`</b>:  Immutable execution context for the current run. 



**Returns:**
 The produced data object. 


---

## <kbd>class</kbd> `ExperimentInput`
Load multiple named artifacts for an experiment.

### <kbd>method</kbd> `ExperimentInput.__init__`

```python
__init__(**inputs: crystallize.core.datasource.DataSource) → None
```






---

#### <kbd>property</kbd> ExperimentInput.replicates







---

### <kbd>method</kbd> `ExperimentInput.fetch`

```python
fetch(ctx: crystallize.core.context.FrozenContext) → dict[str, Any]
```






