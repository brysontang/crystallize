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
from crystallize_extras.ray_plugin.execution import RayExecution
```

Configure the plugin and add it to your experiment:

```python
plugin = RayExecution(address="auto", num_cpus=1, num_gpus=0)
experiment = Experiment(datasource, pipeline, plugins=[plugin])
```

`address` specifies the Ray cluster address, while `num_cpus` and `num_gpus` control the resources allocated to each replicate.
