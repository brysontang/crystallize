---
title: Plugins
description: API reference for experiment lifecycle plugins.
---

## <kbd>module</kbd> `crystallize.plugins.plugins`

### Lifecycle Hooks

Hooks fire in this order during `Experiment.run`:

1. `init_hook(experiment)` – called when the plugin is attached to the experiment.
2. `before_run(experiment)` – once before any replicates start.
3. For each replicate:
   - `before_replicate(experiment, ctx)` – before fetching data and running steps.
   - For each step:
     - `before_step(experiment, step)` – just before the step executes.
     - `after_step(experiment, step, data, ctx)` – immediately after the step finishes and context/metrics are updated.
4. `after_run(experiment, result)` – after all replicates finish and results are aggregated.




**Global Variables**
---------------
- **TYPE_CHECKING**
- **REPLICATE_KEY**
- **CONDITION_KEY**
- **BASELINE_CONDITION**
- **METADATA_FILENAME**
- **SEED_USED_KEY**

---

## <kbd>function</kbd> `default_seed_function`

```python
default_seed_function(seed: 'int') → None
```

Set deterministic seeds for common libraries if available. 


---

## <kbd>class</kbd> `BasePlugin`
Interface for extending the :class:`~crystallize.experiments.experiment.Experiment` lifecycle. 

Subclasses can override any of the hook methods to observe or modify the behaviour of an experiment.  Hooks are called in a well-defined order during :meth:`Experiment.run` allowing plugins to coordinate tasks such as seeding, logging, artifact storage or custom execution strategies. 




---

### <kbd>method</kbd> `BasePlugin.after_run`

```python
after_run(experiment: 'Experiment', result: 'Result') → None
```

Execute cleanup or reporting after :meth:`Experiment.run` completes. 

---

### <kbd>method</kbd> `BasePlugin.after_step`

```python
after_step(
    experiment: 'Experiment',
    step: 'PipelineStep',
    data: 'Any',
    ctx: 'FrozenContext'
) → None
```

Observe results after every :class:`PipelineStep` execution. 

---

### <kbd>method</kbd> `BasePlugin.before_replicate`

```python
before_replicate(experiment: 'Experiment', ctx: 'FrozenContext') → None
```

Run prior to each pipeline execution for a replicate. 

---

### <kbd>method</kbd> `BasePlugin.before_run`

```python
before_run(experiment: 'Experiment') → None
```

Execute logic before :meth:`Experiment.run` begins. 

---

### <kbd>method</kbd> `BasePlugin.before_step`

```python
before_step(experiment: 'Experiment', step: 'PipelineStep') → None
```





---

### <kbd>method</kbd> `BasePlugin.init_hook`

```python
init_hook(experiment: 'Experiment') → None
```

Configure the experiment instance during initialization. 

---

### <kbd>method</kbd> `BasePlugin.run_experiment_loop`

```python
run_experiment_loop(
    experiment: "'Experiment'",
    replicate_fn: 'Callable[[int], Any]'
) → List[Any]
```

Run all replicates and return their results. 

Returning ``NotImplemented`` signals that the plugin does not provide a custom execution strategy and the default should be used instead. 


---

## <kbd>class</kbd> `SeedPlugin`
Manage deterministic seeding for all random operations. 

### <kbd>method</kbd> `SeedPlugin.__init__`

```python
__init__(
    seed: 'Optional[int]' = None,
    auto_seed: 'bool' = True,
    seed_fn: 'Optional[Callable[[int], None]]' = None
) → None
```








---

### <kbd>method</kbd> `SeedPlugin.after_run`

```python
after_run(experiment: 'Experiment', result: 'Result') → None
```

Execute cleanup or reporting after :meth:`Experiment.run` completes. 

---

### <kbd>method</kbd> `SeedPlugin.after_step`

```python
after_step(
    experiment: 'Experiment',
    step: 'PipelineStep',
    data: 'Any',
    ctx: 'FrozenContext'
) → None
```

Observe results after every :class:`PipelineStep` execution. 

---

### <kbd>method</kbd> `SeedPlugin.before_replicate`

```python
before_replicate(experiment: 'Experiment', ctx: 'FrozenContext') → None
```





---

### <kbd>method</kbd> `SeedPlugin.before_run`

```python
before_run(experiment: 'Experiment') → None
```

Execute logic before :meth:`Experiment.run` begins. 

---

### <kbd>method</kbd> `SeedPlugin.before_step`

```python
before_step(experiment: 'Experiment', step: 'PipelineStep') → None
```





---

### <kbd>method</kbd> `SeedPlugin.init_hook`

```python
init_hook(experiment: 'Experiment') → None
```





---

### <kbd>method</kbd> `SeedPlugin.run_experiment_loop`

```python
run_experiment_loop(
    experiment: "'Experiment'",
    replicate_fn: 'Callable[[int], Any]'
) → List[Any]
```

Run all replicates and return their results. 

Returning ``NotImplemented`` signals that the plugin does not provide a custom execution strategy and the default should be used instead. 


---

## <kbd>class</kbd> `LoggingPlugin`
Configure experiment logging using the ``crystallize`` logger. 

### <kbd>method</kbd> `LoggingPlugin.__init__`

```python
__init__(verbose: 'bool' = False, log_level: 'str' = 'INFO') → None
```








---

### <kbd>method</kbd> `LoggingPlugin.after_run`

```python
after_run(experiment: 'Experiment', result: 'Result') → None
```





---

### <kbd>method</kbd> `LoggingPlugin.after_step`

```python
after_step(
    experiment: 'Experiment',
    step: 'PipelineStep',
    data: 'Any',
    ctx: 'FrozenContext'
) → None
```





---

### <kbd>method</kbd> `LoggingPlugin.before_replicate`

```python
before_replicate(experiment: 'Experiment', ctx: 'FrozenContext') → None
```

Run prior to each pipeline execution for a replicate. 

---

### <kbd>method</kbd> `LoggingPlugin.before_run`

```python
before_run(experiment: 'Experiment') → None
```





---

### <kbd>method</kbd> `LoggingPlugin.before_step`

```python
before_step(experiment: 'Experiment', step: 'PipelineStep') → None
```





---

### <kbd>method</kbd> `LoggingPlugin.init_hook`

```python
init_hook(experiment: 'Experiment') → None
```





---

### <kbd>method</kbd> `LoggingPlugin.run_experiment_loop`

```python
run_experiment_loop(
    experiment: "'Experiment'",
    replicate_fn: 'Callable[[int], Any]'
) → List[Any]
```

Run all replicates and return their results. 

Returning ``NotImplemented`` signals that the plugin does not provide a custom execution strategy and the default should be used instead. 


---

## <kbd>class</kbd> `ArtifactPlugin`
Persist artifacts produced during pipeline execution. 

### <kbd>method</kbd> `ArtifactPlugin.__init__`

```python
__init__(
    root_dir: 'str' = './data',
    versioned: 'bool' = False,
    artifact_retention: 'int' = 3,
    big_file_threshold_mb: 'int' = 10
) → None
```








---

### <kbd>method</kbd> `ArtifactPlugin.after_run`

```python
after_run(experiment: 'Experiment', result: 'Result') → None
```





---

### <kbd>method</kbd> `ArtifactPlugin.after_step`

```python
after_step(
    experiment: 'Experiment',
    step: 'PipelineStep',
    data: 'Any',
    ctx: 'FrozenContext'
) → None
```

Write any artifacts logged in ``ctx.artifacts`` to disk. 

---

### <kbd>method</kbd> `ArtifactPlugin.before_replicate`

```python
before_replicate(experiment: 'Experiment', ctx: 'FrozenContext') → None
```

Run prior to each pipeline execution for a replicate. 

---

### <kbd>method</kbd> `ArtifactPlugin.before_run`

```python
before_run(experiment: 'Experiment') → None
```





---

### <kbd>method</kbd> `ArtifactPlugin.before_step`

```python
before_step(experiment: 'Experiment', step: 'PipelineStep') → None
```





---

### <kbd>method</kbd> `ArtifactPlugin.init_hook`

```python
init_hook(experiment: 'Experiment') → None
```

Configure the experiment instance during initialization. 

---

### <kbd>method</kbd> `ArtifactPlugin.run_experiment_loop`

```python
run_experiment_loop(
    experiment: "'Experiment'",
    replicate_fn: 'Callable[[int], Any]'
) → List[Any]
```

Run all replicates and return their results.

Returning ``NotImplemented`` signals that the plugin does not provide a custom execution strategy and the default should be used instead.

---

## <kbd>module</kbd> `crystallize.plugins.provenance`

Plugins for tracking provenance in agentic harness workflows.

---

## <kbd>class</kbd> `PromptProvenancePlugin`

Collect and persist metadata about LLM prompt/response pairs during agentic synthesis.

This plugin monitors context changes after each pipeline step, collecting entries with keys starting with `llm_call`. At the end of the run, it persists all collected calls to JSON files organized by condition.

### <kbd>method</kbd> `PromptProvenancePlugin.__init__`

```python
__init__(artifact_name: str = "llm_calls.json") → None
```

**Parameters:**

- **`artifact_name`**: Filename for the persisted JSON. Default: `"llm_calls.json"`.

**Output location:** `{artifact_dir}/{experiment_id}/v{version}/{condition}/prompts/{artifact_name}`

---

### <kbd>property</kbd> PromptProvenancePlugin.calls_by_condition

```python
@property
def calls_by_condition() -> Mapping[str, List[Mapping[str, Any]]]
```

Returns a copy of collected LLM calls organized by condition name.

---

### <kbd>method</kbd> `PromptProvenancePlugin.before_run`

```python
before_run(experiment: 'Experiment') → None
```

Reset collected calls at the start of each run.

---

### <kbd>method</kbd> `PromptProvenancePlugin.before_replicate`

```python
before_replicate(experiment: 'Experiment', ctx: 'FrozenContext') → None
```

Track the current condition and snapshot existing context keys.

---

### <kbd>method</kbd> `PromptProvenancePlugin.after_step`

```python
after_step(
    experiment: 'Experiment',
    step: 'PipelineStep',
    data: 'Any',
    ctx: 'FrozenContext'
) → None
```

Collect any new `llm_call*` entries added to the context.

---

### <kbd>method</kbd> `PromptProvenancePlugin.after_run`

```python
after_run(experiment: 'Experiment', result: 'Result') → None
```

Persist collected LLM calls to JSON files, one per condition.

---

## <kbd>class</kbd> `EvidenceBundlePlugin`

Persist an evidence bundle linking claim, spec, code, execution outputs, and hypothesis verdicts.

Creates comprehensive audit trails for agentic synthesis workflows. The bundle provides full provenance from the initial claim through to the final verdict.

### <kbd>method</kbd> `EvidenceBundlePlugin.__init__`

```python
__init__(filename: str = "bundle.json") → None
```

**Parameters:**

- **`filename`**: Filename for the persisted bundle. Default: `"bundle.json"`.

**Output location:** `{artifact_dir}/{experiment_id}/v{version}/{condition}/evidence/{filename}`

---

### <kbd>method</kbd> `EvidenceBundlePlugin.after_run`

```python
after_run(experiment: 'Experiment', result: 'Result') → None
```

Build and persist evidence bundles for each condition.

**Bundle structure:**

```json
{
  "condition": "baseline",
  "claims": [{"id": "...", "text": "...", "acceptance": {...}}],
  "specs": [{"allowed_imports": [...], "properties": [...], ...}],
  "code": [{"replicate": 0, "source": "def fit_and_eval(data): ..."}],
  "runs": [{"replicate": 0, "outputs": {"rmse": 0.15, ...}}],
  "metrics": {"rmse": [0.15, 0.14, 0.16], ...},
  "verdicts": [{"hypothesis": "...", "result": {...}, "ranking": {...}}],
  "llm_calls": [...]
}
```

The plugin deduplicates claims and specs across replicates and includes LLM call traces if `PromptProvenancePlugin` is also enabled.
