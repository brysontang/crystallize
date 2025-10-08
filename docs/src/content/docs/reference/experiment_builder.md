---
title: Experiment Builder
---

## <kbd>module</kbd> `crystallize.experiments.experiment_builder`






---

## <kbd>class</kbd> `ExperimentBuilder`
Fluent builder for :class:`Experiment`. 

### <kbd>method</kbd> `ExperimentBuilder.__init__`

```python
__init__(name: 'Optional[str]' = None) → None
```








---

### <kbd>method</kbd> `ExperimentBuilder.add_step`

```python
add_step(step: 'PipelineStep') → 'ExperimentBuilder'
```





---

### <kbd>method</kbd> `ExperimentBuilder.build`

```python
build() → Experiment
```





---

### <kbd>method</kbd> `ExperimentBuilder.datasource`

```python
datasource(datasource: 'DataSource') → 'ExperimentBuilder'
```





---

### <kbd>method</kbd> `ExperimentBuilder.description`

```python
description(description: 'str') → 'ExperimentBuilder'
```





---

### <kbd>method</kbd> `ExperimentBuilder.hypotheses`

```python
hypotheses(hypotheses: 'List[Hypothesis]') → 'ExperimentBuilder'
```





---

### <kbd>method</kbd> `ExperimentBuilder.initial_ctx`

```python
initial_ctx(initial_ctx: 'Dict[str, Any]') → 'ExperimentBuilder'
```





---

### <kbd>method</kbd> `ExperimentBuilder.outputs`

```python
outputs(outputs: 'List[Artifact]') → 'ExperimentBuilder'
```





---

### <kbd>method</kbd> `ExperimentBuilder.pipeline`

```python
pipeline(pipeline: 'Pipeline') → 'ExperimentBuilder'
```





---

### <kbd>method</kbd> `ExperimentBuilder.plugins`

```python
plugins(plugins: 'List[BasePlugin]') → 'ExperimentBuilder'
```





---

### <kbd>method</kbd> `ExperimentBuilder.replicates`

```python
replicates(replicates: 'int') → 'ExperimentBuilder'
```





---

### <kbd>method</kbd> `ExperimentBuilder.treatments`

```python
treatments(treatments: 'List[Treatment]') → 'ExperimentBuilder'
```






