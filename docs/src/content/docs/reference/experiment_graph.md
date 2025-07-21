---
title: Experiment_graph
---


## <kbd>module</kbd> `crystallize.core.experiment_graph`
Orchestrator for chaining multiple experiments via a DAG. 



---

## <kbd>class</kbd> `ExperimentGraph`
Manage and run a directed acyclic graph of experiments. 

### <kbd>method</kbd> `ExperimentGraph.__init__`

```python
__init__() → None
```








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

### <kbd>method</kbd> `ExperimentGraph.from_experiments`

```python
from_experiments(experiments: List[Experiment]) → ExperimentGraph
```

Automatically build a dependency graph by inspecting ``ExperimentInput`` objects.

---

### <kbd>method</kbd> `ExperimentGraph.run`

```python
run(
    treatments: 'List[Treatment] | None' = None,
    replicates: 'int | None' = None
) → Dict[str, Result]
```

Execute all experiments respecting dependency order. 


