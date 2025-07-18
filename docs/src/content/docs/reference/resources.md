---
title: Resources
---


## <kbd>module</kbd> `crystallize.core.resources`






---

## <kbd>class</kbd> `ResourceHandle`
A picklable handle for a resource that should be instantiated once per process. 

### <kbd>method</kbd> `ResourceHandle.__init__`

```python
__init__(factory: 'Callable[[], Any]', resource_id: 'str') → None
```






---

#### <kbd>property</kbd> ResourceHandle.resource

Get or create the resource instance for the current thread/process. 




