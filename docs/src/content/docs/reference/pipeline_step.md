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

Mark a :class:`PipelineStep` as the final step of a pipeline. 

This helper accepts an already constructed step, a factory callable or a ``(factory, params)`` tuple as produced by :func:`pipeline_step`.  The returned object behaves identically to the input but is annotated with the ``is_exit_step`` attribute so that :meth:`Experiment.apply` knows when to stop execution. 


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



---

### <kbd>method</kbd> `PipelineStep.setup`

```python
setup(ctx: crystallize.core.context.FrozenContext) → None
```

Optional hook called once before any replicates run. 

---

### <kbd>method</kbd> `PipelineStep.teardown`

```python
teardown(ctx: crystallize.core.context.FrozenContext) → None
```

Optional hook called once after all replicates finish. 


