---
title: Artifacts
---


## <kbd>module</kbd> `crystallize.core.artifacts`






---

## <kbd>class</kbd> `Artifact`
Container representing a file-like artifact produced by a step. 

### <kbd>method</kbd> `Artifact.__init__`

```python
__init__(name: 'str', data: 'bytes', step_name: 'str') → None
```









---

## <kbd>class</kbd> `ArtifactLog`
Collect artifacts produced during a pipeline step. 

### <kbd>method</kbd> `ArtifactLog.__init__`

```python
__init__() → None
```








---

### <kbd>method</kbd> `ArtifactLog.add`

```python
add(name: 'str', data: 'bytes') → None
```

Append a new artifact to the log. 



**Args:**
 
 - <b>`name`</b>:  Filename for the artifact. 
 - <b>`data`</b>:  Raw bytes to be written to disk by ``ArtifactPlugin``. 

---

### <kbd>method</kbd> `ArtifactLog.clear`

```python
clear() → None
```

Remove all logged artifacts. 


