---
title: Pipeline
---


## <kbd>module</kbd> `crystallize.core.pipeline`




**Global Variables**
---------------
- **TYPE_CHECKING**


---

## <kbd>class</kbd> `Pipeline`
Linear sequence of :class:`PipelineStep` objects forming an experiment workflow. 

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

Run the sequence of steps on ``data`` using ``ctx``. 

Steps may read from or write to the context and record metrics. When a step is marked as cacheable its outputs are stored on disk keyed by its input hash and parameters.  Subsequent runs will reuse cached results if available. 



**Args:**
 
 - <b>`data`</b>:  Raw input from a :class:`DataSource`. 
 - <b>`ctx`</b>:  Immutable execution context shared across steps. 



**Returns:**
 Either the pipeline output or ``(output, provenance)`` when ``return_provenance`` is ``True``. The provenance list contains a record per step detailing cache hits and context mutations. 

---

### <kbd>method</kbd> `Pipeline.signature`

```python
signature() → str
```

Hash‐friendly signature for caching/provenance. 


