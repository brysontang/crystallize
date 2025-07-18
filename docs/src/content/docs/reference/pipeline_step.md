---
title: Pipeline_step
---


## <kbd>module</kbd> `crystallize.core.pipeline_step`






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


