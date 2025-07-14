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
    datasource: 'Optional[DataSource]' = None,
    pipeline: 'Optional[Pipeline]' = None,
    treatments: 'Optional[List[Treatment]]' = None,
    hypotheses: 'Optional[List[Hypothesis]]' = None,
    replicates: 'int' = 1,
    plugins: 'Optional[List[BasePlugin]]' = None
) → None
```








---

### <kbd>method</kbd> `Experiment.apply`

```python
apply(
    treatment_name: 'Optional[str]' = None,
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

### <kbd>method</kbd> `Experiment.run`

```python
run() → Result
```

Execute the experiment, using serial execution if no plugin provides it. 

---

### <kbd>method</kbd> `Experiment.validate`

```python
validate() → None
```






