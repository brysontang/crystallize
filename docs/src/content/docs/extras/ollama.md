---
title: Ollama Client Initialization
description: Pipeline step for creating an Ollama client
---

The `initialize_ollama_client` step creates an `ollama.Client` instance and stores it in the experiment context.

## Installation

```bash
pip install crystallize-extras[ollama]
```

## Usage

```python
from crystallize_extras.ollama_step.initialize import initialize_ollama_client

```

Add the step to your pipeline:

```python
step = initialize_ollama_client(base_url="http://localhost:11434")
pipeline = Pipeline([step, ...])
```

The client is stored under the key `ollama_client` by default, but you can customize this with the `context_key` parameter.
