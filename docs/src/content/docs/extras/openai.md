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
from crystallize_extras.openai_step import (
    initialize_openai_client,
    initialize_async_openai_client,
)

init_client = initialize_openai_client(
    client_options={"base_url": "https://api.openai.com/v1"}
)

pipeline = Pipeline([
    init_client,
    call_openai(),
])
```

- The wrapper stores a `resource_factory` under `openai_client` (override with `context_key`). Retrieve the client later via `ctx.get("openai_client")(ctx)`.
- Use the async variant with `AsyncExecution` if your downstream steps are `async def`.
- The extras package raises an informative ImportError if the official `openai` SDK is not installed.
