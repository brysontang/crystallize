from crystallize import data_source, pipeline_step
from crystallize.core.experiment import Experiment
from crystallize.core.pipeline import Pipeline
from crystallize.core.plugins import ArtifactPlugin

@data_source
def source(ctx):
    return [1, 2, 3]

@pipeline_step()
def save_data(data, ctx):
    import pandas as pd

    df = pd.DataFrame({"values": data})
    csv = df.to_csv(index=False).encode()
    ctx.artifacts.add("data.csv", csv)
    return data

exp1 = Experiment(
    datasource=source(),
    pipeline=Pipeline([save_data()]),
    plugins=[ArtifactPlugin(root_dir="artifact_chain", versioned=True)],
)
exp1.validate()

if __name__ == "__main__":
    exp1.run(replicates=2)
