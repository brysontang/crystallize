---
title: Treatment
---

## <kbd>module</kbd> `crystallize.experiments.treatment`






---

## <kbd>class</kbd> `Treatment`
Set up initial context values for a replicate. 

Unlike plugins, a treatment does not hook into the execution lifecycle; it simply mutates the :class:`FrozenContext` before the pipeline starts.  The ``apply`` argument can be a callable or a mapping providing the context additions. 



**Args:**
 
 - <b>`name`</b>:  Human-readable identifier for the treatment. 
 - <b>`apply`</b>:  Either a callable ``apply(ctx)`` or a mapping of keys to insert.  Existing keys must not be mutated—``FrozenContext`` enforces this  immutability. 

### <kbd>method</kbd> `Treatment.__init__`

```python
__init__(
    name: str,
    apply: Union[Callable[[crystallize.utils.context.FrozenContext], Any], Mapping[str, Any]]
)
```






---

#### <kbd>property</kbd> Treatment.apply_map







---

### <kbd>method</kbd> `Treatment.apply`

```python
apply(ctx: crystallize.utils.context.FrozenContext) → None
```

Apply the treatment to the execution context. 

Implementations typically add new keys like: 

 ctx['embed_dim'] = 512  ctx.override(step='hpo', param_space={'lr': [1e-4, 5e-5]}) 



**Raises:**
  ContextMutationError if attempting to overwrite existing keys. 


