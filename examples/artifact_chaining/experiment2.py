from experiment1 import exp1

from crystallize import pipeline_step
from crystallize.core.experiment import Experiment
from crystallize.core.pipeline import Pipeline


@pipeline_step()
def load_and_use(path, ctx):
    import pandas as pd

    df = pd.read_csv(path)
    ctx.metrics.add("length", len(df))
    return {"length": len(df)}


exp2 = Experiment(
    datasource=exp1.artifact_datasource(step="SaveData", name="data.csv"),
    pipeline=Pipeline([load_and_use()]),
)
exp2.validate()

if __name__ == "__main__":
    result = exp2.run()
    print(result.metrics.baseline.metrics)
