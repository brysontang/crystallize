---
title: Datasource
---

## <kbd>module</kbd> `crystallize.datasources.datasource`




**Global Variables**
---------------
- **TYPE_CHECKING**


---

## <kbd>class</kbd> `DataSource`
Abstract provider of input data for an experiment. 




---

### <kbd>method</kbd> `DataSource.fetch`

```python
fetch(ctx: 'FrozenContext') → Any
```

Return raw data for a single pipeline run. 

Implementations may load data from disk, generate synthetic samples or access remote sources.  They should be deterministic with respect to the provided context. 



**Args:**
 
 - <b>`ctx`</b>:  Immutable execution context for the current run. 



**Returns:**
 The produced data object. 


---

## <kbd>class</kbd> `ExperimentInput`
Bundles multiple named datasources for an experiment. 

This can include both raw datasources (like functions decorated with @data_source) and Artifacts that link to the output of other experiments. 

### <kbd>method</kbd> `ExperimentInput.__init__`

```python
__init__(**inputs: 'DataSource') → None
```



**Args:**
 
 - <b>`**inputs`</b>:  A keyword mapping of names to DataSource objects. 


---

#### <kbd>property</kbd> ExperimentInput.replicates

The number of replicates, inferred from Artifact inputs. 



---

### <kbd>method</kbd> `ExperimentInput.fetch`

```python
fetch(ctx: 'FrozenContext') → dict[str, Any]
```

Fetches data from all contained datasources. 


---

## <kbd>class</kbd> `ExperimentInput`
Bundles multiple named datasources for an experiment. 

This can include both raw datasources (like functions decorated with @data_source) and Artifacts that link to the output of other experiments. 

### <kbd>method</kbd> `ExperimentInput.__init__`

```python
__init__(**inputs: 'DataSource') → None
```



**Args:**
 
 - <b>`**inputs`</b>:  A keyword mapping of names to DataSource objects. 


---

#### <kbd>property</kbd> ExperimentInput.replicates

The number of replicates, inferred from Artifact inputs. 



---

### <kbd>method</kbd> `ExperimentInput.fetch`

```python
fetch(ctx: 'FrozenContext') → dict[str, Any]
```

Fetches data from all contained datasources. 


