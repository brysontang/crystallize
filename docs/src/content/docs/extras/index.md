---
title: Extras & Integrations
description: Optional plugins and steps shipped in the crystallize-extras package.
---

Crystallize ships optional integrations in the `crystallize-extras` package. Install the extras you need and import their plugins/steps in your experiments.

## Installation Cheatsheet

| Integration | Install command | What it adds |
| --- | --- | --- |
| RayExecution | `pip install --upgrade --pre crystallize-extras[ray]` | Distributed replicate execution via Ray. |
| vLLM | `pip install --upgrade --pre crystallize-extras[vllm]` | Pipeline step to initialize and cache a vLLM engine. |
| Ollama | `pip install --upgrade --pre crystallize-extras[ollama]` | Pipeline steps to create sync/async Ollama clients. |
| OpenAI | `pip install --upgrade --pre crystallize-extras[openai]` | Pipeline steps to create sync/async OpenAI clients. |

If the extras package is missing, the CLI prompts you to install it when loading experiments that reference these integrations.

## Usage Links

- [RayExecution Plugin](./ray)
- [vLLM Engine Initialization](./vllm)
- [Ollama Client Initialization](./ollama)
- [OpenAI Client Initialization](./openai)
