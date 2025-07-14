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
Immutable execution context with safe mutation helpers. 

### <kbd>method</kbd> `FrozenContext.__init__`

```python
__init__(initial: Mapping[str, Any]) → None
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
Proxy for :class:`FrozenContext` that logs key reads. 

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






