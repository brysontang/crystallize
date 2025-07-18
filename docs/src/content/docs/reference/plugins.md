---
title: Plugins
---


## <kbd>module</kbd> `crystallize.core.plugins`




**Global Variables**
---------------
- **TYPE_CHECKING**

---

## <kbd>function</kbd> `default_seed_function`

```python
default_seed_function(seed: 'int') → None
```

Set deterministic seeds for common libraries if available. 


---

## <kbd>class</kbd> `BasePlugin`
Interface for extending the :class:`~crystallize.core.experiment.Experiment` lifecycle. 

Subclasses can override any of the hook methods to observe or modify the behaviour of an experiment.  Hooks are called in a well-defined order during :meth:`Experiment.run` allowing plugins to coordinate tasks such as seeding, logging, artifact storage or custom execution strategies. 




---

### <kbd>method</kbd> `BasePlugin.after_run`

```python
after_run(experiment: 'Experiment', result: 'Result') → None
```

Execute cleanup or reporting after :meth:`Experiment.run` completes.
Writes ``metadata.json`` containing the experiment id and replicate count.

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
Configure logging verbosity and experiment progress reporting. 

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
    root_dir: 'str' = './crystallize_artifacts',
    versioned: 'bool' = False
) → None
```








---

### <kbd>method</kbd> `ArtifactPlugin.after_run`

```python
after_run(experiment: 'Experiment', result: 'Result') → None
```

Execute cleanup or reporting after :meth:`Experiment.run` completes. 

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


