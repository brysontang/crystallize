import subprocess
import sys
from pathlib import Path

import pytest

from crystallize.utils.context import FrozenContext
from crystallize.datasources.datasource import DataSource
from crystallize.pipelines.pipeline_step import PipelineStep
from crystallize import verifier


class DummyDataSource(DataSource):
    def fetch(self, ctx: FrozenContext):
        return ctx.as_dict().get("value", 0)


class PassStep(PipelineStep):
    cacheable = False

    def __call__(self, data, ctx):
        ctx.metrics.add("metric", data)
        return {"metric": data}

    @property
    def params(self):
        return {}


@verifier
def always_sig(baseline, treatment):
    return {"p_value": 0.01, "significant": True, "accepted": True}


def rank_p(res: dict) -> float:
    return res["p_value"]


def apply_value(ctx: FrozenContext, amount: int) -> None:
    ctx.add("value", amount)


@pytest.fixture
def experiment_yaml(tmp_path: Path) -> Path:
    exp = tmp_path / "exp"
    exp.mkdir()
    (exp / "datasources.py").write_text(
        "from crystallize import data_source\n"
        "@data_source\n"
        "def src(ctx):\n    return 0\n"
    )
    (exp / "steps.py").write_text(
        "from crystallize import pipeline_step\n"
        "@pipeline_step()\n"
        "def step(data, ctx):\n    ctx.metrics.add('metric', data)\n    return {'metric': data}\n"
    )
    (exp / "hypotheses.py").write_text(
        "from crystallize import verifier\n"
        "@verifier\n"
        "def always_sig(baseline, treatment):\n    return {'p_value':0.01,'significant':True}\n"
    )
    config = {
        "name": "exp",
        "datasource": {"d": "src"},
        "steps": ["step"],
        "treatments": [{"name": "increment", "amount": 1}],
        "hypotheses": [{"name": "h", "verifier": "always_sig", "metrics": "metric"}],
    }
    import yaml

    (exp / "config.yaml").write_text(yaml.safe_dump(config))
    return exp / "config.yaml"


def test_cli_runs_from_yaml(experiment_yaml: Path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "crystallize.yaml_cli.main",
            "run",
            str(experiment_yaml),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    out = result.stdout
    assert "Hypothesis Results" in out
    assert "increment" in out
    assert "Yes" in out
