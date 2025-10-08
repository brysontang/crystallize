---
title: Ollama Client Initialization
description: Pipeline step for creating an Ollama client
---

The `initialize_ollama_client` step creates an `ollama.Client` instance and stores it in the experiment context.

## Installation

```bash
pip install --upgrade --pre crystallize-extras[ollama]
```

## Usage

```python
from crystallize_extras.ollama_step import (
    initialize_ollama_client,
    initialize_async_ollama_client,
)

init_sync = initialize_ollama_client(host="http://localhost:11434")
init_async = initialize_async_ollama_client(host="http://localhost:11434")

pipeline = Pipeline([
    init_sync,
    call_ollama(),
])
```

- The step stores a `resource_factory` under `ollama_client` (override via `context_key`). Later steps can retrieve the client with `client = ctx.get("ollama_client")(ctx)`.
- Use the async variant when your pipeline runs under `AsyncExecution`.
- If `ollama` is missing, the step raises an ImportError suggesting the extras installation command.
