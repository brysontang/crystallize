---
title: Injection
---

## <kbd>module</kbd> `crystallize.utils.injection`





---

## <kbd>function</kbd> `inject_from_ctx`

```python
inject_from_ctx(fn: 'Callable[..., Any]') → Callable[..., Any]
```

Inject missing parameters from ``ctx`` when calling ``fn``. 

Parameters not explicitly provided will be looked up in the given :class:`FrozenContext` using their parameter name. If a value is not present in the context, the parameter's default is used. 


