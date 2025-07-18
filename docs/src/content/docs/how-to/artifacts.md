---
title: Saving Artifacts
description: Persist models, plots, or other files produced during pipeline steps.
---

Crystallize steps can produce files like trained models or plots. Use `ArtifactPlugin` to automatically save these artifacts to a structured directory.

## 1. Enable the Plugin

```python
from crystallize.core.experiment import Experiment
from crystallize.core.pipeline import Pipeline
from crystallize.core.pipeline_step import PipelineStep
from crystallize.core.plugins import ArtifactPlugin


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

## Chaining via Importable Datasources

After an experiment runs with `ArtifactPlugin`, you can import the experiment in
another file and load its artifacts automatically. The datasource provides a
file path for each replicate, letting you choose how to load the contents:

```python
# experiment1.py
exp1.run(replicates=2)

from pathlib import Path

# experiment2.py
from experiment1 import exp1

from crystallize.core.experiment import Experiment
from crystallize.core.pipeline import Pipeline, pipeline_step


@pipeline_step()
def load_json(path, ctx):
    import json
    return json.loads(Path(path).read_text())

exp2 = Experiment(
    datasource=exp1.artifact_datasource(step="ModelStep", name="data.json"),
    pipeline=Pipeline([load_json()]),
)
exp2.validate()
exp2.run()  # replicates set from metadata
```

`artifact_datasource()` reads `<root>/<id>/v<version>/metadata.json` to set the
replicate count and will raise an error if you provide a different count when
running the new experiment.
