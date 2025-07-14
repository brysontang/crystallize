---
title: Pipeline_step
---


## <kbd>module</kbd> `crystallize.core.pipeline_step`





---

## <kbd>function</kbd> `exit_step`

```python
exit_step(
    item: Union[crystallize.core.pipeline_step.PipelineStep, Callable[..., crystallize.core.pipeline_step.PipelineStep], Tuple[Callable[..., crystallize.core.pipeline_step.PipelineStep], Dict[str, Any]]]
) → Union[crystallize.core.pipeline_step.PipelineStep, Callable[..., crystallize.core.pipeline_step.PipelineStep]]
```

Mark a :class:`PipelineStep` as an exit point. Handles instances, factories, or parameterized tuples. 


---

## <kbd>class</kbd> `PipelineStep`





---

#### <kbd>property</kbd> PipelineStep.params

Parameters of this step for hashing and caching. 



**Returns:**
 
 - <b>`dict`</b>:  Parameters dictionary. 

---

#### <kbd>property</kbd> PipelineStep.step_hash

Unique hash identifying this step based on its parameters. 




