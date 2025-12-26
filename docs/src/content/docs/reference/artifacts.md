---
title: Artifacts
---

## <kbd>module</kbd> `crystallize.plugins.artifacts`

### Directory Structure

`ArtifactPlugin` writes artifacts under:

```
{root_dir}/{experiment_name}/v{version}/replicate_{rep}/{condition}/{step_name}/{artifact_name}
```

- `root_dir` defaults to `./data`.
- `version` is `0` unless `versioned=True`, in which case each run increments `v1`, `v2`, etc.
- Metrics live in `{root_dir}/{experiment_name}/v{version}/{condition}/results.json` alongside a `_manifest.json` and `.crystallize_complete` marker. Experiment metadata is stored in `{root_dir}/{experiment_name}/v{version}/metadata.json`.

### Versioning & Pruning

- When `versioned=True`, each run creates a new `v{N}` directory. `versioned=False` reuses `v0`.
- `artifact_retention` controls how many versions to keep (default `3`, override with `CRYSTALLIZE_ARTIFACT_RETENTION`; `<=0` keeps all). Versions outside the retention window are pruned down to metrics only (artifacts removed).
- `big_file_threshold_mb` (default `10`, env `CRYSTALLIZE_BIG_FILE_THRESHOLD_MB`) is applied to all retained-but-not-latest versions: files larger than the threshold are removed, keeping manifests and `results.json` intact.
- The latest version always keeps all artifacts; older kept versions drop oversized files; pruned versions keep only metrics for auditability.




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

