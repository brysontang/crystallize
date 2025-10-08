---
title: Experiment Graph
---

## <kbd>module</kbd> `crystallize.experiments.experiment_graph`
Orchestrator for chaining multiple experiments via a DAG. 

**Global Variables**
---------------
- **BASELINE_CONDITION**

---

## <kbd>function</kbd> `find_experiments_root`

```python
find_experiments_root(start: 'Path', strict: 'bool' = True) → Path
```

Walk up from *start* until we find a directory that either **is** called 'experiments' or **contains** a sub-directory called 'experiments'. 

If not found: 
  - when ``strict=True`` (default), raise FileNotFoundError (explicit failure). 
  - when ``strict=False``, return ``start`` and log a warning. 


---

## <kbd>class</kbd> `ExperimentGraph`
Manage and run a directed acyclic graph of experiments. 

### <kbd>method</kbd> `ExperimentGraph.__init__`

```python
__init__(*experiments: 'Experiment', name: 'str | None' = None) → None
```

Create a graph and optionally infer dependencies from experiments. 




---

### <kbd>method</kbd> `ExperimentGraph.add_dependency`

```python
add_dependency(downstream: 'Experiment', upstream: 'Experiment') → None
```

Add an edge from ``upstream`` to ``downstream``. 

---

### <kbd>method</kbd> `ExperimentGraph.add_experiment`

```python
add_experiment(experiment: 'Experiment') → None
```

Add an experiment node to the graph. 

---

### <kbd>method</kbd> `ExperimentGraph.arun`

```python
arun(
    treatments: 'List[Treatment] | None' = None,
    replicates: 'int | None' = None,
    strategy: 'str | None' = None,
    progress_callback: 'Callable[[str, str], Awaitable[None]] | None' = None
) → Dict[str, Result]
```

Execute all experiments respecting dependency order. 

---

### <kbd>classmethod</kbd> `ExperimentGraph.from_experiments`

```python
from_experiments(experiments: 'List[Experiment]') → 'ExperimentGraph'
```

Construct a graph automatically from experiment dependencies. 

Parameters 
---------- experiments:  List of all experiments that form the workflow. 

Returns 
------- ExperimentGraph  Fully built and validated experiment graph. 

---

### <kbd>classmethod</kbd> `ExperimentGraph.from_yaml`

```python
from_yaml(config: 'str | Path') → 'ExperimentGraph'
```

Load an experiment graph starting from ``config``. 

The ``config`` argument should point to a ``config.yaml`` file for the final experiment. All upstream experiments referenced via ``experiment#artifact`` notation are discovered recursively in sibling directories. 

---

### <kbd>method</kbd> `ExperimentGraph.run`

```python
run(
    treatments: 'List[Treatment] | None' = None,
    replicates: 'int | None' = None,
    strategy: 'str | None' = None
) → Dict[str, Result]
```

Synchronous wrapper for the async arun method. 

---

### <kbd>classmethod</kbd> `ExperimentGraph.visualize_from_yaml`

```python
visualize_from_yaml(config: 'str | Path') → None
```

Print dependencies and execution order for a YAML graph. 


