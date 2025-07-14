---
title: Cache
---


## <kbd>module</kbd> `crystallize.core.cache`





---

## <kbd>function</kbd> `compute_hash`

```python
compute_hash(obj: Any) → str
```

Compute sha256 hash of object's pickle representation. 


---

## <kbd>function</kbd> `cache_path`

```python
cache_path(step_hash: str, input_hash: str) → Path
```






---

## <kbd>function</kbd> `load_cache`

```python
load_cache(step_hash: str, input_hash: str) → Any
```






---

## <kbd>function</kbd> `store_cache`

```python
store_cache(step_hash: str, input_hash: str, data: Any) → None
```






