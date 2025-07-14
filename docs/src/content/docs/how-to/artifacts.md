---
title: Saving Artifacts
description: Persist models, plots, or other files produced during pipeline steps.
---

Crystallize steps can produce files like trained models or plots. Use `ArtifactPlugin` to automatically save these artifacts to a structured directory.

## 1. Enable the Plugin

```python
from crystallize.core.plugins import ArtifactPlugin
from crystallize.core.experiment import Experiment
from crystallize.core.pipeline import Pipeline
from crystallize.core.pipeline_step import PipelineStep

class ModelStep(PipelineStep):
    def __call__(self, data, ctx):
        ctx.artifacts.add("model.bin", b"binary data")
        return data

    @property
    def params(self):
        return {}

exp = Experiment(
    datasource=my_source(),
    pipeline=Pipeline([ModelStep()]),
    plugins=[ArtifactPlugin(root_dir="artifacts", versioned=True)],
)
exp.validate()
exp.run()
```

Artifacts are stored under:
`<root>/<experiment_id>/v<run>/<replicate>/<condition>/<step>/<name>`.
