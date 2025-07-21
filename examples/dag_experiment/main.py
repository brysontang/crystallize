from __future__ import annotations

import json
from pathlib import Path

from crystallize import data_source, pipeline_step
from crystallize import (
    ArtifactPlugin,
    Experiment,
    ExperimentGraph,
    MultiArtifactDataSource,
    Pipeline,
    Treatment,
    FrozenContext,
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
def average(data: list[float], ctx: FrozenContext) -> float:
    """Compute the average value adjusted by a ``factor`` parameter."""
    factor = ctx.get("factor", 1.0)
    avg = sum(data) / len(data) * factor
    ctx.artifacts.add(
        "average.json", json.dumps({"avg": avg}).encode()
    )
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


temp_exp = Experiment(
    datasource=temperatures(),
    pipeline=Pipeline([average()]),
    plugins=[ArtifactPlugin(root_dir="dag_output", versioned=True)],
    name="temperature_stats",
)
temp_exp.validate()

humidity_exp = Experiment(
    datasource=humidities(),
    pipeline=Pipeline([average()]),
    plugins=[ArtifactPlugin(root_dir="dag_output", versioned=True)],
    name="humidity_stats",
)
humidity_exp.validate()

comfort_ds = MultiArtifactDataSource(
    temp=temp_exp.artifact_datasource(step="AverageStep", name="average.json"),
    humidity=humidity_exp.artifact_datasource(step="AverageStep", name="average.json"),
)

comfort_exp = Experiment(
    datasource=comfort_ds,
    pipeline=Pipeline([comfort_index()]),
    name="comfort_index",
)
comfort_exp.validate()


if __name__ == "__main__":
    graph = ExperimentGraph()
    for exp in (temp_exp, humidity_exp, comfort_exp):
        graph.add_experiment(exp)
    graph.add_dependency(comfort_exp, temp_exp)
    graph.add_dependency(comfort_exp, humidity_exp)

    print("Baseline run:")
    base = graph.run()
    print(base["comfort_index"].metrics.baseline.metrics)

    treatment = Treatment("scaled", {"factor": 1.5})
    print("\nWith treatment:")
    treated = graph.run(treatments=[treatment])
    print(treated["comfort_index"].metrics.treatments["scaled"].metrics)
