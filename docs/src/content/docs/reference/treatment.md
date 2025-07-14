---
title: Treatment
---


## <kbd>module</kbd> `crystallize.core.treatment`






---

## <kbd>class</kbd> `Treatment`
A named mutator that tweaks parameters for an experiment replicate. 



**Args:**
 
 - <b>`name`</b>:  Human-readable identifier. 
 - <b>`apply`</b>:  Either a callable ``apply(ctx)`` or a mapping of key-value pairs  to add to the context. The callable form allows dynamic logic while  the mapping form simply inserts the provided keys. Existing keys  must not be mutated – ``FrozenContext`` enforces immutability. 

### <kbd>method</kbd> `Treatment.__init__`

```python
__init__(
    name: str,
    apply: Union[Callable[[crystallize.core.context.FrozenContext], Any], Mapping[str, Any]]
)
```








---

### <kbd>method</kbd> `Treatment.apply`

```python
apply(ctx: crystallize.core.context.FrozenContext) → None
```

Apply the treatment to the execution context. 

Implementations typically add new keys like: 

 ctx['embed_dim'] = 512  ctx.override(step='hpo', param_space={'lr': [1e-4, 5e-5]}) 



**Raises:**
  ContextMutationError if attempting to overwrite existing keys. 


