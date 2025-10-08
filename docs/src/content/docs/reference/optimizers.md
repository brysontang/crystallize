---
title: Optimizers
---

## <kbd>module</kbd> `crystallize.experiments.optimizers`






---

## <kbd>class</kbd> `Objective`
Defines the optimization goal. 

### <kbd>method</kbd> `Objective.__init__`

```python
__init__(
    metric: 'Union[str, List[str]]',
    direction: 'Union[str, List[str]]'
) → None
```









---

## <kbd>class</kbd> `BaseOptimizer`
The abstract base class for all optimization strategies. 

### <kbd>method</kbd> `BaseOptimizer.__init__`

```python
__init__(objective: 'Objective')
```








---

### <kbd>method</kbd> `BaseOptimizer.ask`

```python
ask() → list[Treatment]
```

Suggest one or more Treatments for the next trial. 

---

### <kbd>method</kbd> `BaseOptimizer.get_best_treatment`

```python
get_best_treatment() → Treatment
```

Return the best treatment found after all trials. 

---

### <kbd>method</kbd> `BaseOptimizer.tell`

```python
tell(objective_values: 'dict[str, float]') → None
```

Provide the aggregated objective value(s) for the last trial. 


