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
from crystallize_extras.vllm_step import initialize_llm_engine

init_engine = initialize_llm_engine(engine_options={"model": "mistral"})
pipeline = Pipeline([init_engine, generate_predictions()])
```

- The step runs during pipeline setup, storing a `resource_factory` under the context key (default `llm_engine`).
- Access the cached engine inside later steps: `engine = ctx.get("llm_engine")(ctx)`.
- Pass a different `context_key` if you need multiple engines.

If `vllm` is not installed, the step raises an informative error suggesting `pip install crystallize-extras[vllm]`.
