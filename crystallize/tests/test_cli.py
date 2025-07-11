import subprocess
import sys
from ast import literal_eval
from pathlib import Path

import pytest

from crystallize.core.context import FrozenContext
from crystallize.core.datasource import DataSource
from crystallize.core.pipeline_step import PipelineStep
from crystallize import verifier


class DummyDataSource(DataSource):
    def fetch(self, ctx: FrozenContext):
        return ctx.as_dict().get("value", 0)


class PassStep(PipelineStep):
    def __call__(self, data, ctx):
        return {"metric": data}

    @property
    def params(self):
        return {}


@verifier
def always_sig(baseline, treatment):
    return {"p_value": 0.01, "significant": True, "accepted": True}


def apply_value(ctx: FrozenContext, amount: int) -> None:
    ctx.add("value", amount)


@pytest.fixture
def experiment_yaml(tmp_path: Path) -> Path:
    yaml_path = tmp_path / "exp.yaml"
    yaml_path.write_text(
        """
replicates: 2
datasource:
  target: crystallize.tests.test_cli.DummyDataSource
  params: {}
pipeline:
  - target: crystallize.tests.test_cli.PassStep
    params: {}
hypothesis:
  metric: metric
  verifier:
    target: crystallize.tests.test_cli.always_sig
    params: {}
treatments:
  - name: increment
    apply:
      target: crystallize.tests.test_cli.apply_value
      params:
        amount: 1
"""
    )
    return yaml_path


def test_cli_runs_from_yaml(experiment_yaml: Path):
    result = subprocess.run(
        [sys.executable, "-m", "crystallize.cli.main", "run", str(experiment_yaml)],
        capture_output=True,
        text=True,
        check=True,
    )
    output = literal_eval(result.stdout.strip())
    assert output["metric"]["increment"]["significant"] is True
    assert output["metric"]["increment"]["accepted"] is True
