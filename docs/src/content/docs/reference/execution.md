---
title: Execution
---

## <kbd>module</kbd> `crystallize.plugins.execution`

Execution is delegated out of `Experiment` into two collaborators:

- An execution plugin (e.g., `SerialExecution`, `ParallelExecution`, or `AsyncExecution`) that drives the replicate loop via `run_experiment_loop`.
- `ResultAggregator` (from `crystallize.experiments.aggregation`) which collates replicate outputs, seeds, provenance, and metrics into a `Result`.

`Experiment.run/arun` selects the strategy plugin, passes in the replicate callable, and then hands the collected replicate results to `ResultAggregator`. Override or swap these collaborators instead of subclassing `Experiment` to change aggregation behavior; the legacy `_aggregate_results` hook is no longer part of the execution path.




**Global Variables**
---------------
- **TYPE_CHECKING**
- **VALID_EXECUTOR_TYPES**


---

## <kbd>class</kbd> `SerialExecution`
Execute replicates one after another within the main process. 

### <kbd>method</kbd> `SerialExecution.__init__`

```python
__init__(progress: 'bool' = False) → None
```








---

### <kbd>method</kbd> `SerialExecution.run_experiment_loop`

```python
run_experiment_loop(
    experiment: "'Experiment'",
    replicate_fn: 'Callable[[int], Any]'
) → List[Any]
```






---

## <kbd>class</kbd> `ParallelExecution`
Run SYNC replicates concurrently using ThreadPoolExecutor or ProcessPoolExecutor. 

### <kbd>method</kbd> `ParallelExecution.__init__`

```python
__init__(
    max_workers: 'Optional[int]' = None,
    executor_type: 'str' = 'thread',
    progress: 'bool' = False
) → None
```








---

### <kbd>method</kbd> `ParallelExecution.run_experiment_loop`

```python
run_experiment_loop(
    experiment: "'Experiment'",
    replicate_fn: 'Callable[[int], Any]'
) → List[Any]
```






---

## <kbd>class</kbd> `AsyncExecution`
Run async replicates concurrently using asyncio.gather. 

### <kbd>method</kbd> `AsyncExecution.__init__`

```python
__init__(progress: 'bool' = False) → None
```








---

### <kbd>method</kbd> `AsyncExecution.run_experiment_loop`

```python
run_experiment_loop(
    experiment: "'Experiment'",
    replicate_fn: 'Callable[[int], Any]'
) → List[Any]
```





