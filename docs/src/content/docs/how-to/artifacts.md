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
`<root>/<experiment_name_or_id>/v<run>/<replicate>/<condition>/<step>/<name>`.

## Chaining via Importable Datasources

After an experiment runs with `ArtifactPlugin`, you can import the experiment in
another file and load its artifacts automatically. The datasource provides a
`Path` object for each replicate, letting you choose how to load the contents:

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
    return json.loads(path.read_text())

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
It works even if `exp1` hasn't been executed in this file—the experiment name or
pipeline signature locates the correct directory.

### Loading CSV with Pandas

Because the datasource only yields file paths, you can load data in any format.

```python
@pipeline_step()
def load_csv(path, ctx):
    import pandas as pd
    return pd.read_csv(path)

exp_csv = Experiment(
    datasource=exp1.artifact_datasource(step="ModelStep", name="data.csv"),
    pipeline=Pipeline([load_csv()]),
)
```

Set ``require_metadata=True`` when you want to ensure metadata exists and raise
an error if the previous run lacked `ArtifactPlugin`.
