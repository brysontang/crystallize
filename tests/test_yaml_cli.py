import subprocess
import sys
from ast import literal_eval
from pathlib import Path

from crystallize.core.context import FrozenContext
from crystallize.core.datasource import DataSource
from crystallize.core.pipeline_step import PipelineStep
from crystallize.core.stat_test import StatisticalTest


class DummyDataSource(DataSource):
    def fetch(self, ctx: FrozenContext):
        return ctx.as_dict().get("value", 0)


class PassStep(PipelineStep):
    def __call__(self, data, ctx):
        return {"metric": data}

    @property
    def params(self):
        return {}


class AlwaysSig(StatisticalTest):
    def run(self, baseline, treatment, *, alpha: float = 0.05):
        return {"p_value": 0.01, "significant": True}


def apply_value(ctx: FrozenContext, amount: int) -> None:
    ctx["value"] = amount


def test_cli_runs_from_yaml(tmp_path: Path):
    yaml_path = tmp_path / "exp.yaml"
    yaml_path.write_text(
        """
{
  "replicates": 1,
  "datasource": {"target": "tests.test_yaml_cli.DummyDataSource", "params": {}},
  "pipeline": [{"target": "tests.test_yaml_cli.PassStep", "params": {}}],
  "hypothesis": {
    "metric": "metric",
    "direction": "increase",
    "statistical_test": {"target": "tests.test_yaml_cli.AlwaysSig", "params": {}}
  },
  "treatments": [
    {
      "name": "inc",
      "apply": {"target": "tests.test_yaml_cli.apply_value", "params": {"amount": 1}}
    }
  ]
}
"""
    )

    result = subprocess.run(
        [sys.executable, "-m", "crystallize.recur", "run", str(yaml_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    output = literal_eval(result.stdout.strip())
    assert output["significant"] is True
    assert output["accepted"] is True
