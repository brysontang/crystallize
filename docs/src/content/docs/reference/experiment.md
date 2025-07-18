---
title: Experiment
---


## <kbd>module</kbd> `crystallize.core.experiment`




**Global Variables**
---------------
- **VALID_EXECUTOR_TYPES**


---

## <kbd>class</kbd> `Experiment`




### <kbd>method</kbd> `Experiment.__init__`

```python
__init__(
    datasource: 'DataSource',
    pipeline: 'Pipeline',
    plugins: 'Optional[List[BasePlugin]]' = None
) → None
```

Instantiate an experiment configuration. 



**Args:**
 
 - <b>`datasource`</b>:  Object that provides the initial data for each run. 
 - <b>`pipeline`</b>:  Pipeline executed for every replicate. 
 - <b>`plugins`</b>:  Optional list of plugins controlling experiment behaviour. 




---

### <kbd>method</kbd> `Experiment.apply`

```python
apply(
    treatment: 'Treatment | None' = None,
    data: 'Any | None' = None,
    seed: 'Optional[int]' = None
) → Any
```

Run the pipeline once with optional treatment and return outputs. 

---

### <kbd>method</kbd> `Experiment.get_plugin`

```python
get_plugin(plugin_class: 'type') → Optional[BasePlugin]
```

Return the first plugin instance matching ``plugin_class``. 

---

### <kbd>method</kbd> `Experiment.optimize`

```python
optimize(
    optimizer: "'BaseOptimizer'",
    num_trials: 'int',
    replicates_per_trial: 'int' = 1
) → Treatment
```





---

### <kbd>method</kbd> `Experiment.run`

```python
run(
    treatments: 'List[Treatment] | None' = None,
    hypotheses: 'List[Hypothesis] | None' = None,
    replicates: 'int | None' = None
) → Result
```

Execute the experiment and return a :class:`Result` instance. 

The lifecycle proceeds as follows: 

1. ``before_run`` hooks for all plugins are invoked. 2. Each replicate is executed via ``run_experiment_loop``.  The default  implementation runs serially, but plugins may provide parallel or  distributed strategies. 3. After all replicates complete, metrics are aggregated and  hypotheses are verified. 4. ``after_run`` hooks for all plugins are executed. 

The returned :class:`~crystallize.core.result.Result` contains aggregated metrics, any captured errors and a provenance record of context mutations for every pipeline step.

---

### <kbd>method</kbd> `Experiment.artifact_datasource`

```python
artifact_datasource(
    step: 'str',
    name: 'str' = 'data.json',
    condition: 'str' = 'baseline',
    *,
    require_metadata: 'bool' = False
) → DataSource
```

Return a datasource that yields a :class:`pathlib.Path` for each replicate. The
datasource reads from
`<root>/<id>/v<version>/replicate_<rep>/<condition>/<step>/<name>` and sets its
``replicates`` attribute from ``metadata.json`` when available. When
``require_metadata`` is ``True`` and the metadata file is missing a
``FileNotFoundError`` is raised.

---

### <kbd>method</kbd> `Experiment.validate`

```python
validate() → None
```






