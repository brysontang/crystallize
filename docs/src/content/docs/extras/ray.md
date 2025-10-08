---
title: RayExecution Plugin
description: Run experiment replicates in parallel using Ray
---

The `RayExecution` plugin allows Crystallize experiments to distribute replicate execution on a Ray cluster.

## Installation

```bash
pip install --upgrade --pre crystallize-extras[ray]
```

## Usage

```python
from crystallize_extras.ray_plugin import RayExecution

plugin = RayExecution(address="auto", num_cpus=1, num_gpus=0)
experiment = Experiment(
    datasource=my_source(),
    pipeline=my_pipeline,
    plugins=[plugin],
)
```

- `address="auto"` connects to the local Ray runtime. Point it at a cluster URL if needed.
- `num_cpus` and `num_gpus` describe the resources each replicate reserves.
- If Ray is not installed, the plugin raises an informative error prompting you to install `crystallize-extras[ray]`.

After the run completes, `RayExecution.after_run` shuts down the Ray runtime if this process initialised it.
