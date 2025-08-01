---
title: OpenAI Client Initialization
description: Pipeline step for creating an OpenAI client
---

The `initialize_openai_client` step creates an `openai.OpenAI` instance and stores it in the experiment context.

## Installation

```bash
pip install --upgrade --pre crystallize-extras[openai]
```

## Usage

```python
from crystallize_extras.openai_step.initialize import initialize_openai_client

```

Add the step to your pipeline:

```python
step = initialize_openai_client(client_options={"base_url": "http://api.openai.com/v1"})
pipeline = Pipeline([step, ...])
```

The client is stored under the key `openai_client` by default, but you can customize this with the `context_key` parameter.
