---
title: Execution
---


## <kbd>module</kbd> `crystallize.core.execution`




**Global Variables**
---------------
- **TYPE_CHECKING**
- **VALID_EXECUTOR_TYPES**


---

## <kbd>class</kbd> `SerialExecution`
Default serial execution strategy. 

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
Run replicates concurrently using a pool executor. 

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






