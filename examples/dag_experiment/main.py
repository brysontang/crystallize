from __future__ import annotations

import json
from pathlib import Path

from crystallize import (
    Artifact,
    ArtifactPlugin,
    Experiment,
    ExperimentGraph,
    ExperimentInput,
    FrozenContext,
    Pipeline,
    Treatment,
    data_source,
    pipeline_step,
)


@data_source
def temperatures(ctx: FrozenContext) -> list[int]:
    """Provide daily temperature readings."""
    return [20, 22, 21]


@data_source
def humidities(ctx: FrozenContext) -> list[float]:
    """Provide daily humidity measurements."""
    return [0.4, 0.5, 0.45]


@pipeline_step()
def average(data: list[float], ctx: FrozenContext, out: Artifact) -> float:
    """Compute the average value adjusted by a ``factor`` parameter."""
    factor = ctx.get("factor", 1.0)
    avg = sum(data) / len(data) * factor
    out.write(json.dumps({"avg": avg}).encode())
    return avg


@pipeline_step()
def comfort_index(data: dict[str, Path], ctx: FrozenContext) -> float:
    """Combine averages to produce a simple comfort index."""
    with open(data["temp"]) as f:
        temp_avg = json.load(f)["avg"]
    with open(data["humidity"]) as f:
        humidity_avg = json.load(f)["avg"]
    index = temp_avg - humidity_avg
    ctx.metrics.add("comfort", index)
    return index


out_temp = Artifact("average.json")
temp_exp = Experiment(
    datasource=temperatures(),
    pipeline=Pipeline([average(out=out_temp)]),
    plugins=[ArtifactPlugin(root_dir="dag_output", versioned=True)],
    name="temperature_stats",
    outputs=[out_temp],
)
temp_exp.validate()  # optional

out_humidity = Artifact("average.json")
humidity_exp = Experiment(
    datasource=humidities(),
    pipeline=Pipeline([average(out=out_humidity)]),
    plugins=[ArtifactPlugin(root_dir="dag_output", versioned=True)],
    name="humidity_stats",
    outputs=[out_humidity],
)
humidity_exp.validate()  # optional

comfort_ds = ExperimentInput(
    temp=temp_exp.artifact_datasource(step="AverageStep", name="average.json"),
    humidity=humidity_exp.artifact_datasource(step="AverageStep", name="average.json"),
)

comfort_exp = Experiment(
    datasource=comfort_ds,
    pipeline=Pipeline([comfort_index()]),
    name="comfort_index",
)
comfort_exp.validate()  # optional


if __name__ == "__main__":
    graph = ExperimentGraph.from_experiments([temp_exp, humidity_exp, comfort_exp])

    print("Baseline run:")
    base = graph.run()
    print(base["comfort_index"].metrics.baseline.metrics)

    treatment = Treatment("scaled", {"factor": 1.5})
    print("\nWith treatment:")
    treated = graph.run(treatments=[treatment])
    print(treated["comfort_index"].metrics.treatments["scaled"].metrics)
