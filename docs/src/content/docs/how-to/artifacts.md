---
title: Saving Artifacts
description: Persist models, plots, or other files produced during pipeline steps.
---

Crystallize steps can produce files like trained models or plots. Use `ArtifactPlugin` to automatically save these artifacts to a structured directory.

## 1. Enable the Plugin

```python
from crystallize import Experiment, Pipeline, Artifact
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize.plugins.plugins import ArtifactPlugin


class ModelStep(PipelineStep):
    def __init__(self, out: Artifact):
        self.out = out

    def __call__(self, data, ctx):
        self.out.write(b"binary data")
        return data

    @property
    def params(self):
        return {}

out = Artifact("model.bin")
exp = Experiment(
    datasource=my_source(),
    pipeline=Pipeline([ModelStep(out)]),
    plugins=[ArtifactPlugin(root_dir="artifacts", versioned=True)],
    outputs=[out],
)
exp.validate()  # optional
exp.run()
```

Loader callables must be pickleable when using process-based execution.
Crystallize automatically wraps lambda functions so they can be used as
artifact loaders.

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

from crystallize import Experiment, pipeline_step
from crystallize.pipelines.pipeline import Pipeline


@pipeline_step()
def load_json(data, ctx):
    import json
    return json.loads(data.read_text())

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
def load_csv(data, ctx):
    import pandas as pd
    return pd.read_csv(data)

exp_csv = Experiment(
    datasource=exp1.artifact_datasource(step="ModelStep", name="data.csv"),
    pipeline=Pipeline([load_csv()]),
)
```

Set `require_metadata=True` when you want to ensure metadata exists and raise
an error if the previous run lacked `ArtifactPlugin`.

## Resuming Experiments

Artifacts also enable resuming long experiments. Pass `strategy="resume"` to
`Experiment.run()` or `ExperimentGraph.run()` and Crystallize will skip any
conditions that already wrote a completion marker. Metrics from the previous
run are loaded so the results dictionary is fully populated. Downstream
experiments are rerun only when their required outputs are missing.
