from concurrent.futures import ThreadPoolExecutor
import asyncio

import pytest

from crystallize.datasources.datasource import DataSource
from crystallize.experiments.experiment import Experiment
from crystallize.pipelines.pipeline import Pipeline
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize.plugins.execution import (
    ParallelExecution,
    SerialExecution,
    AsyncExecution,
)


class DummyExperiment:
    def __init__(self, reps: int) -> None:
        self.replicates = reps


class DummyDS(DataSource):
    def fetch(self, ctx):
        return 1


class UnpicklableStep(PipelineStep):
    def __init__(self) -> None:
        self.fh = open(__file__, "r")

    def __call__(self, data, ctx):
        return data

    @property
    def params(self) -> dict:
        return {}


def test_serial_execution_progress(monkeypatch):
    called = []

    def fake_tqdm(iterable, *args, **kwargs):
        called.append(kwargs.get("desc"))
        return iterable

    monkeypatch.setattr("tqdm.tqdm", fake_tqdm)
    exec_plugin = SerialExecution(progress=True)
    exp = DummyExperiment(3)
    async def rep_fn(i: int) -> int:
        return i

    result = asyncio.run(exec_plugin.run_experiment_loop(exp, rep_fn))
    assert result == [0, 1, 2]
    assert called == ["Replicates"]


def test_parallel_execution_thread(monkeypatch):
    called = []

    def fake_tqdm(iterable, *args, **kwargs):
        called.append(kwargs.get("desc"))
        return iterable

    monkeypatch.setattr("tqdm.tqdm", fake_tqdm)
    exec_plugin = ParallelExecution(progress=True)
    exp = DummyExperiment(3)
    result = exec_plugin.run_experiment_loop(exp, lambda i: i * 2)
    assert sorted(result) == [0, 2, 4]
    assert called == ["Replicates"]


def test_parallel_execution_process(monkeypatch):
    called = []

    def fake_tqdm(iterable, *args, **kwargs):
        called.append(kwargs.get("desc"))
        return iterable

    monkeypatch.setattr("tqdm.tqdm", fake_tqdm)
    monkeypatch.setattr(
        "crystallize.plugins.execution.ProcessPoolExecutor", ThreadPoolExecutor
    )
    monkeypatch.setattr(
        "crystallize.experiments.experiment._run_replicate_remote",
        lambda args: args[1] * 3,
    )
    exec_plugin = ParallelExecution(progress=True, executor_type="process")
    exp = DummyExperiment(3)
    result = exec_plugin.run_experiment_loop(exp, lambda x: x)
    assert sorted(result) == [0, 3, 6]
    assert called == ["Replicates"]


def test_parallel_execution_process_pickling_error(monkeypatch):
    class ExplodingExecutor:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            pass

        def submit(self, fn, arg):
            import pickle

            pickle.dumps(arg)
            return None

    monkeypatch.setattr(
        "crystallize.plugins.execution.ProcessPoolExecutor", ExplodingExecutor
    )
    pipeline = Pipeline([UnpicklableStep()])
    exp = Experiment(datasource=DummyDS(), pipeline=pipeline, name="bad-exp")
    exec_plugin = ParallelExecution(executor_type="process")

    with pytest.raises(RuntimeError) as excinfo:
        exec_plugin.run_experiment_loop(exp, lambda i: i)

    msg = str(excinfo.value)
    assert "bad-exp" in msg
    assert "resource_factory" in msg
    assert "UnpicklableStep" in msg


def test_parallel_execution_invalid_type():
    exec_plugin = ParallelExecution(executor_type="bad")
    with pytest.raises(ValueError):
        exec_plugin.run_experiment_loop(DummyExperiment(1), lambda i: i)


def test_parallel_execution_async_suggests_async_plugin():
    exec_plugin = ParallelExecution()
    exp = DummyExperiment(1)

    async def rep_fn(i: int) -> int:
        return i

    with pytest.raises(TypeError) as excinfo:
        exec_plugin.run_experiment_loop(exp, rep_fn)
    assert "AsyncExecution" in str(excinfo.value)


def test_async_execution_progress(monkeypatch):
    called = []

    async def fake_gather(*tasks, **kwargs):
        called.append(kwargs.get("desc"))
        return await asyncio.gather(*tasks)

    monkeypatch.setattr("tqdm.asyncio.tqdm.gather", fake_gather)
    exec_plugin = AsyncExecution(progress=True)
    exp = DummyExperiment(3)

    async def rep_fn(i: int) -> int:
        await asyncio.sleep(0)
        return i

    result = asyncio.run(exec_plugin.run_experiment_loop(exp, rep_fn))
    assert result == [0, 1, 2]
    assert called == ["Replicates"]


def test_async_execution_falls_back_to_asyncio(monkeypatch):
    called = []
    real_gather = asyncio.gather

    async def fake_asyncio_gather(*tasks, **kwargs):
        called.append(True)
        return await real_gather(*tasks, **kwargs)

    async def fail(*_args, **_kwargs):
        raise RuntimeError("tqdm gather should not be called")

    monkeypatch.setattr(asyncio, "gather", fake_asyncio_gather)
    monkeypatch.setattr("tqdm.asyncio.tqdm.gather", fail)
    exec_plugin = AsyncExecution(progress=True)
    exp = DummyExperiment(1)

    async def rep_fn(i: int) -> int:
        return i

    result = asyncio.run(exec_plugin.run_experiment_loop(exp, rep_fn))
    assert result == [0]
    assert called == [True]
