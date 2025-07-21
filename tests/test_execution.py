from concurrent.futures import ThreadPoolExecutor

import pytest

from crystallize.plugins.execution import ParallelExecution, SerialExecution


class DummyExperiment:
    def __init__(self, reps: int) -> None:
        self.replicates = reps


def test_serial_execution_progress(monkeypatch):
    called = []

    def fake_tqdm(iterable, *args, **kwargs):
        called.append(kwargs.get("desc"))
        return iterable

    monkeypatch.setattr("tqdm.tqdm", fake_tqdm)
    exec_plugin = SerialExecution(progress=True)
    exp = DummyExperiment(3)
    result = exec_plugin.run_experiment_loop(exp, lambda i: i)
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
        "crystallize.experiments.experiment._run_replicate_remote", lambda args: args[1] * 3
    )
    exec_plugin = ParallelExecution(progress=True, executor_type="process")
    exp = DummyExperiment(3)
    result = exec_plugin.run_experiment_loop(exp, lambda x: x)
    assert sorted(result) == [0, 3, 6]
    assert called == ["Replicates"]


def test_parallel_execution_invalid_type():
    exec_plugin = ParallelExecution(executor_type="bad")
    with pytest.raises(ValueError):
        exec_plugin.run_experiment_loop(DummyExperiment(1), lambda i: i)
