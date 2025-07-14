---
title: Pipeline
---


## <kbd>module</kbd> `crystallize.core.pipeline`




**Global Variables**
---------------
- **TYPE_CHECKING**


---

## <kbd>class</kbd> `Pipeline`
Linear sequence of :class:`PipelineStep` objects. 

### <kbd>method</kbd> `Pipeline.__init__`

```python
__init__(steps: List[crystallize.core.pipeline_step.PipelineStep]) → None
```








---

### <kbd>method</kbd> `Pipeline.get_provenance`

```python
get_provenance() → List[Mapping[str, Any]]
```

Return immutable provenance from the last run. 

---

### <kbd>method</kbd> `Pipeline.run`

```python
run(
    data: Any,
    ctx: crystallize.core.context.FrozenContext,
    verbose: bool = False,
    progress: bool = False,
    rep: Optional[int] = None,
    condition: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
    return_provenance: bool = False,
    experiment: Optional[ForwardRef('Experiment')] = None
) → Union[Any, Tuple[Any, List[Mapping[str, Any]]]]
```

Execute the pipeline in order. 



**Args:**
 
 - <b>`data`</b>:  Raw data from a DataSource. 
 - <b>`ctx`</b>:   Immutable execution context. 



**Returns:**
 If ``return_provenance`` is ``False`` (default), returns the output from the last step. Otherwise returns a tuple ``(output, provenance)`` where ``provenance`` is a list of step records. 

---

### <kbd>method</kbd> `Pipeline.signature`

```python
signature() → str
```

Hash‐friendly signature for caching/provenance. 


