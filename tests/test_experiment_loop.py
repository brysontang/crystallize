import asyncio
from types import ModuleType
from pathlib import Path
from typing import Any

from crystallize import (
    data_source,
    pipeline_step,
    Experiment,
    Pipeline,
    Artifact,
    ExperimentGraph,
)
from crystallize.plugins.plugins import ArtifactPlugin
from crystallize.loops.experiment_loop import (
    ExperimentLoop,
    ConvergenceCondition,
    MutationSpec,
)
from crystallize.utils.constants import BASELINE_CONDITION
from crystallize.utils.context import FrozenContext
from crystallize.datasources.datasource import DataSource


@data_source
def num_source(ctx):
    return ctx.get("val", 0)


@pipeline_step()
def write_out(data, ctx, out: Artifact):
    out.write(str(data).encode())
    return data

STEP_DIR = "Write_OutStep"


@pipeline_step()
def add_key_step(data, ctx, key: str) -> Any:
    ctx.add(key, 1)
    return data


class ArtifactReader(DataSource):
    def __init__(
        self, plugin: ArtifactPlugin, exp: Experiment, artifact: Artifact, step: str
    ) -> None:
        self.plugin = plugin
        self.exp = exp
        self.artifact = artifact
        self.step = step
        self.required_outputs = [artifact]
        self.replicates = 1

    def fetch(self, ctx: FrozenContext) -> Any:
        ver = self.plugin.version
        base = Path(self.plugin.root_dir) / (self.exp.name or self.exp.id) / f"v{ver}"
        path = (
            base
            / "replicate_0"
            / BASELINE_CONDITION
            / self.step
            / self.artifact.name
        )
        return path


@pipeline_step()
def eval_step(data: Path, ctx):
    val = int(Path(data).read_text())
    score = val / 10
    ctx.metrics.add("score", score)
    return score


def make_loop(
    tmp_path: Path,
    max_iters: int,
    threshold: float,
    patience: int = 1,
    *,
    mutate_context: bool = False,
) -> tuple[ExperimentLoop, ArtifactPlugin]:
    art_plugin = ArtifactPlugin(root_dir=str(tmp_path / "arts"))
    out_art = Artifact("out.txt")
    steps = []
    if mutate_context:
        steps.append(add_key_step(key="extra"))
    steps.append(write_out(out=out_art))
    gen = Experiment(
        datasource=num_source(),
        pipeline=Pipeline(steps),
        plugins=[art_plugin],
        name="gen",
        initial_ctx={"val": 0},
        outputs=[out_art],
    )
    gen.validate()

    reader_ds = ArtifactReader(art_plugin, gen, out_art, STEP_DIR)
    eval_exp = Experiment(
        datasource=reader_ds,
        pipeline=Pipeline([eval_step()]),
        plugins=[ArtifactPlugin(root_dir=str(tmp_path / "arts"))],
        name="eval",
    )
    eval_exp.validate()

    graph = ExperimentGraph(name="loop")
    graph.add_experiment(gen)
    graph.add_experiment(eval_exp)
    graph.add_dependency(eval_exp, gen)

    cond = ConvergenceCondition(
        experiment="eval",
        metric="score",
        condition=BASELINE_CONDITION,
        operator=">",
        threshold=threshold,
        patience=patience,
    )

    module = ModuleType("loader")

    def incr(path: Path) -> int:
        return int(path.read_text()) + 1

    module.increment = incr

    mut = MutationSpec(
        experiment="gen",
        treatment=BASELINE_CONDITION,
        replace_context_key="val",
        from_artifact="gen#out.txt",
        loader="increment",
    )

    loop = ExperimentLoop(
        graph,
        "eval",
        max_iters,
        [cond],
        [mut],
        module,
    )
    return loop, art_plugin


def test_loop_runs_max_iters(tmp_path: Path) -> None:
    loop, plugin = make_loop(tmp_path, 3, threshold=100)
    asyncio.run(loop.arun())
    base = Path(plugin.root_dir) / "gen"
    assert (base / "v0").exists()
    assert (base / "v1").exists()
    assert (base / "v2").exists()


def test_loop_mutates_context(tmp_path: Path) -> None:
    loop, plugin = make_loop(tmp_path, 2, threshold=100)
    asyncio.run(loop.arun())
    base = Path(plugin.root_dir) / "gen"
    final = base / "v1" / "replicate_0" / BASELINE_CONDITION / STEP_DIR / "out.txt"
    assert final.read_text() == "1"


def test_loop_resets_between_runs(tmp_path: Path) -> None:
    loop, plugin = make_loop(tmp_path, 2, threshold=100)
    asyncio.run(loop.arun())
    first_v0 = (
        Path(plugin.root_dir)
        / "gen"
        / "v0"
        / "replicate_0"
        / BASELINE_CONDITION
        / STEP_DIR
        / "out.txt"
    )
    assert first_v0.read_text() == "0"

    asyncio.run(loop.arun())
    second_v0 = (
        Path(plugin.root_dir)
        / "gen"
        / "v0"
        / "replicate_0"
        / BASELINE_CONDITION
        / STEP_DIR
        / "out.txt"
    )
    assert second_v0.read_text() == "0"


def test_loop_clears_mutated_keys(tmp_path: Path) -> None:
    loop, _ = make_loop(tmp_path, 1, threshold=100, mutate_context=True)
    asyncio.run(loop.arun())
    # run again; should not raise due to existing key
    asyncio.run(loop.arun())
