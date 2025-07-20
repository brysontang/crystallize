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

## <kbd>class</kbd> `MultiArtifactDataSource`
Aggregate multiple artifact datasources into one. 

### <kbd>method</kbd> `MultiArtifactDataSource.__init__`

```python
__init__(**kwargs: crystallize.core.datasource.DataSource) → None
```






---

#### <kbd>property</kbd> MultiArtifactDataSource.replicates







---

### <kbd>method</kbd> `MultiArtifactDataSource.fetch`

```python
fetch(ctx: crystallize.core.context.FrozenContext) → dict[str, Any]
```






