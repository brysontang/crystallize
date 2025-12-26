---
title: Provenance
---

## <kbd>module</kbd> `crystallize.plugins.provenance`
Plugins that persist provenance for agentic harness executions. 

**Global Variables**
---------------
- **BASELINE_CONDITION**
- **CONDITION_KEY**


---

## <kbd>class</kbd> `PromptProvenancePlugin`
Collect and persist metadata about LLM prompt/response pairs. 

### <kbd>method</kbd> `PromptProvenancePlugin.__init__`

```python
__init__(artifact_name: 'str' = 'llm_calls.json') → None
```






---

#### <kbd>property</kbd> PromptProvenancePlugin.calls_by_condition







---

### <kbd>method</kbd> `PromptProvenancePlugin.after_run`

```python
after_run(experiment, result) → None
```





---

### <kbd>method</kbd> `PromptProvenancePlugin.after_step`

```python
after_step(experiment, step, data, ctx) → None
```





---

### <kbd>method</kbd> `PromptProvenancePlugin.before_replicate`

```python
before_replicate(experiment, ctx) → None
```





---

### <kbd>method</kbd> `PromptProvenancePlugin.before_run`

```python
before_run(experiment) → None
```






---

## <kbd>class</kbd> `EvidenceBundlePlugin`
Persist an evidence bundle linking claim, spec, code, tests and verdicts. 

### <kbd>method</kbd> `EvidenceBundlePlugin.__init__`

```python
__init__(filename: 'str' = 'bundle.json') → None
```








---

### <kbd>method</kbd> `EvidenceBundlePlugin.after_run`

```python
after_run(experiment, result) → None
```






