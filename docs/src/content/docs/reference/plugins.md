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
Abstract base class for creating plugins that hook into the Experiment lifecycle. 




---

### <kbd>method</kbd> `BasePlugin.after_run`

```python
after_run(experiment: 'Experiment', result: 'Result') → None
```

Called at the end of ``Experiment.run()`` after the ``Result`` object is created. 

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

Called after each ``PipelineStep`` is executed. 

---

### <kbd>method</kbd> `BasePlugin.before_replicate`

```python
before_replicate(experiment: 'Experiment', ctx: 'FrozenContext') → None
```

Called before each replicate's pipeline is executed. 

---

### <kbd>method</kbd> `BasePlugin.before_run`

```python
before_run(experiment: 'Experiment') → None
```

Called at the beginning of ``Experiment.run()``, before any replicates start. 

---

### <kbd>method</kbd> `BasePlugin.init_hook`

```python
init_hook(experiment: 'Experiment') → None
```

Called during ``Experiment.__init__`` to configure the experiment instance. 

---

### <kbd>method</kbd> `BasePlugin.run_experiment_loop`

```python
run_experiment_loop(
    experiment: "'Experiment'",
    replicate_fn: 'Callable[[int], Any]'
) → List[Any]
```

Run replicates and return results or ``NotImplemented``. 


---

## <kbd>class</kbd> `SeedPlugin`
Plugin handling deterministic seeding. 

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

Called at the end of ``Experiment.run()`` after the ``Result`` object is created. 

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

Called after each ``PipelineStep`` is executed. 

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

Called at the beginning of ``Experiment.run()``, before any replicates start. 

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

Run replicates and return results or ``NotImplemented``. 


---

## <kbd>class</kbd> `LoggingPlugin`
Plugin configuring logging verbosity and output. 

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

Called before each replicate's pipeline is executed. 

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

Run replicates and return results or ``NotImplemented``. 


---

## <kbd>class</kbd> `ArtifactPlugin`
Plugin that saves artifacts logged during pipeline execution. 

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

Called at the end of ``Experiment.run()`` after the ``Result`` object is created. 

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





---

### <kbd>method</kbd> `ArtifactPlugin.before_replicate`

```python
before_replicate(experiment: 'Experiment', ctx: 'FrozenContext') → None
```

Called before each replicate's pipeline is executed. 

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

Called during ``Experiment.__init__`` to configure the experiment instance. 

---

### <kbd>method</kbd> `ArtifactPlugin.run_experiment_loop`

```python
run_experiment_loop(
    experiment: "'Experiment'",
    replicate_fn: 'Callable[[int], Any]'
) → List[Any]
```

Run replicates and return results or ``NotImplemented``. 


