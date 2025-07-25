---
title: Context
---


## <kbd>module</kbd> `crystallize.core.context`






---

## <kbd>class</kbd> `ContextMutationError`
Raised when attempting to mutate an existing key in FrozenContext. 





---

## <kbd>class</kbd> `FrozenMetrics`
Immutable mapping of metric lists with safe append. 

### <kbd>method</kbd> `FrozenMetrics.__init__`

```python
__init__() → None
```








---

### <kbd>method</kbd> `FrozenMetrics.add`

```python
add(key: str, value: Any) → None
```





---

### <kbd>method</kbd> `FrozenMetrics.as_dict`

```python
as_dict() → Mapping[str, Tuple[Any, ...]]
```






---

## <kbd>class</kbd> `FrozenContext`
Immutable execution context shared between pipeline steps. 

Once a key is set its value cannot be modified. Attempting to do so raises :class:`ContextMutationError`. This immutability guarantees deterministic provenance during pipeline execution. 



**Attributes:**
 
 - <b>`metrics`</b>:  :class:`FrozenMetrics` used to accumulate lists of metric  values. 
- <b>`artifacts`</b>:  :class:`ArtifactLog` collecting binary artifacts to be saved
- <b>`by `</b>: class:`~crystallize.core.plugins.ArtifactPlugin`.
- <b>`logger`</b>:  :class:`logging.Logger` used for debug and info messages.

### <kbd>method</kbd> `FrozenContext.__init__`

```python
__init__(
    initial: Mapping[str, Any],
    logger: Optional[logging.Logger] = None,
) → None
```








---

### <kbd>method</kbd> `FrozenContext.add`

```python
add(key: str, value: Any) → None
```

Alias for ``__setitem__`` providing a clearer API. 

---

### <kbd>method</kbd> `FrozenContext.as_dict`

```python
as_dict() → Mapping[str, Any]
```





---

### <kbd>method</kbd> `FrozenContext.get`

```python
get(key: str, default: Optional[Any] = None) → Any
```

Return the value for ``key`` if present else ``default``. 


---

## <kbd>class</kbd> `LoggingContext`
Proxy around :class:`FrozenContext` that records all key accesses. 

### <kbd>method</kbd> `LoggingContext.__init__`

```python
__init__(
    ctx: crystallize.core.context.FrozenContext,
    logger: logging.Logger
) → None
```








---

### <kbd>method</kbd> `LoggingContext.add`

```python
add(key: str, value: Any) → None
```





---

### <kbd>method</kbd> `LoggingContext.as_dict`

```python
as_dict() → Mapping[str, Any]
```





---

### <kbd>method</kbd> `LoggingContext.get`

```python
get(key: str, default: Optional[Any] = None) → Any
```






