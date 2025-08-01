---
title: vLLM Engine Initialization
description: Pipeline step for creating a vLLM engine
---

The `initialize_llm_engine` step creates a `vllm.LLM` instance and stores it in the experiment context.

## Installation

```bash
pip install --upgrade --pre crystallize-extras[vllm]
```

## Usage

```python
from crystallize_extras.vllm_step.initialize import initialize_llm_engine
```

Add the step to your pipeline:

```python
step = initialize_llm_engine(engine_options={"model": "mistral"})
pipeline = Pipeline([step, ...])
```

The engine is stored under the key `llm_engine` by default, but you can customize this with the `context_key` parameter.
