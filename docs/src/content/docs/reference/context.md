---
title: Context
---

## <kbd>module</kbd> `crystallize.utils.context`






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
 
     - <b>`metrics`</b>:  :class:`FrozenMetrics` used to accumulate lists of metric values. artifacts: :class:`ArtifactLog` collecting binary artifacts to be saved 
     - <b>`by `</b>: class:`~crystallize.plugins.plugins.ArtifactPlugin`. logger: :class:`logging.Logger` used for debug and info messages. 

### <kbd>method</kbd> `FrozenContext.__init__`

```python
__init__(
    initial: Mapping[str, Any],
    logger: Optional[logging.Logger] = None
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
A FrozenContext proxy that records every key read and emits DEBUG lines. 

Parameters 
---------- ctx:  The original, immutable context created by the Experiment runner. logger:  The logger to use for DEBUG instrumentation. 

### <kbd>method</kbd> `LoggingContext.__init__`

```python
__init__(
    ctx: crystallize.utils.context.FrozenContext,
    logger: Optional[logging.Logger] = None
)
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






