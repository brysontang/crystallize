import asyncio
from types import ModuleType
from crystallize import Experiment, Pipeline, data_source, pipeline_step
from crystallize.experiments.experiment_graph import ExperimentGraph
from crystallize.loops.experiment_loop import ExperimentLoop
from crystallize.plugins.plugins import ArtifactPlugin
from crystallize_extras.openai_step.initialize_async import initialize_async_openai_client

class DummyAsyncClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

@data_source
def ds(ctx):
    return 0

@pipeline_step()
def no_op(data, ctx):
    return data

def make_loop(tmp_path):
    steps = [initialize_async_openai_client(client_options={}), no_op()]
    exp = Experiment(datasource=ds(), pipeline=Pipeline(steps), plugins=[ArtifactPlugin(root_dir=str(tmp_path))], name="gen")
    exp.validate()
    graph = ExperimentGraph.from_experiments([exp])
    dummy_mod = ModuleType("dummy")
    return ExperimentLoop(graph, "gen", 1, [], [], dummy_mod)

def test_loop_clears_openai_context(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "crystallize_extras.openai_step.initialize_async.AsyncOpenAI",
        DummyAsyncClient,
    )
    loop = make_loop(tmp_path)
    asyncio.run(loop.arun())
    asyncio.run(loop.arun())
