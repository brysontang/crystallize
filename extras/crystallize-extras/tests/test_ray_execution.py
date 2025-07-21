import pytest
from crystallize.experiments.experiment import Experiment
from crystallize.pipelines.pipeline import Pipeline
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize.datasources.datasource import DataSource
from crystallize.utils.context import FrozenContext

from crystallize_extras.ray_plugin.execution import RayExecution


class DummyDataSource(DataSource):
    def fetch(self, ctx: FrozenContext):
        return 0


class DummyRay:
    def __init__(self):
        self.initialized = False
        self.init_args = None
        self.remote_configs = []
        self.shutdown_called = False

    def is_initialized(self):
        return self.initialized

    def init(self, address=None):
        self.initialized = True
        self.init_args = address

    def remote(self, num_cpus=1, num_gpus=0):
        def decorator(fn):
            self.remote_configs.append((num_cpus, num_gpus))

            class RemoteFunc:
                def __init__(self, f):
                    self.f = f

                def remote(self, *args, **kwargs):
                    return self.f(*args, **kwargs)

            return RemoteFunc(fn)

        return decorator

    def get(self, futures):
        return list(futures)

    def shutdown(self):
        self.shutdown_called = True
        self.initialized = False


class DummyStep(PipelineStep):
    def __call__(self, data, ctx):
        return data

    @property
    def params(self):
        return {}


def test_ray_execution_plugin(monkeypatch):
    dummy_ray = DummyRay()
    monkeypatch.setattr('crystallize_extras.ray_plugin.execution.ray', dummy_ray)

    plugin = RayExecution(address='auto', num_cpus=2, num_gpus=0)
    exp = Experiment(datasource=DummyDataSource(), pipeline=Pipeline([DummyStep()]))
    plugin.init_hook(exp)
    assert dummy_ray.initialized is True
    assert dummy_ray.init_args == 'auto'

    results = plugin.run_experiment_loop(exp, lambda r: r)
    assert results == [0]
    assert dummy_ray.remote_configs == [(2, 0)]

    plugin.after_run(exp, None)
    assert dummy_ray.shutdown_called is True

def test_ray_execution_missing_dependency(monkeypatch):
    from crystallize_extras import ray_plugin

    monkeypatch.setattr(ray_plugin.execution, "ray", None)
    plugin = ray_plugin.execution.RayExecution()
    exp = Experiment(datasource=DummyDataSource(), pipeline=Pipeline([DummyStep()]))
    with pytest.raises(ImportError):
        plugin.init_hook(exp)
