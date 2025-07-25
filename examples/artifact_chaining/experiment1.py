from crystallize import data_source, pipeline_step, Artifact
from crystallize import Experiment
from crystallize.pipelines.pipeline import Pipeline
from crystallize.plugins.plugins import ArtifactPlugin

@data_source
def source(ctx):
    return [1, 2, 3]

@pipeline_step()
def save_data(data, ctx, out: Artifact):
    import pandas as pd

    df = pd.DataFrame({"values": data})
    csv = df.to_csv(index=False).encode()
    out.write(csv)
    return data

out_file = Artifact("data.csv")
exp1 = Experiment(
    datasource=source(),
    pipeline=Pipeline([save_data(out=out_file)]),
    plugins=[ArtifactPlugin(root_dir="artifact_chain", versioned=True)],
    outputs=[out_file],
)
exp1.validate()  # optional

if __name__ == "__main__":
    exp1.run(replicates=2)
