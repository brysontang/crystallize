---
title: Artifacts
---

## <kbd>module</kbd> `crystallize.plugins.artifacts`




**Global Variables**
---------------
- **BASELINE_CONDITION**

---

## <kbd>function</kbd> `load_metrics`

```python
load_metrics(
    exp_dir: 'Path',
    version: 'int | None' = None
) → Tuple[int, dict[str, Any], dict[str, dict[str, Any]]]
```

Load metrics from ``results.json`` files for ``version``. 

Parameters 
---------- exp_dir:  Base directory of the experiment. version:  Version number to load from. If ``None``, the latest version is used. Returns 
------- Tuple of the loaded version number, baseline metrics and a mapping of treatment name to metrics in stable order. 


---

## <kbd>function</kbd> `load_all_metrics`

```python
load_all_metrics(
    exp_dir: 'Path',
    version: 'int | None' = None
) → Tuple[int, dict[str, Any], dict[str, Tuple[int, dict[str, Any]]]]
```

Load metrics for all treatments across versions. 

Parameters 
---------- exp_dir:  Base directory of the experiment. version:  Latest version to consider. If ``None`` the newest version on disk is  used. 

Returns 
------- Tuple of the latest version number, baseline metrics from that version and a mapping of treatment name to a tuple of ``(version, metrics)`` where ``version`` indicates which artifact version the metrics were loaded from. 


