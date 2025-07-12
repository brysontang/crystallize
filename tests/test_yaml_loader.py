import json
from pathlib import Path

import pytest

from crystallize.cli.yaml_loader import load_experiment, load_experiment_from_file
from crystallize import data_source, pipeline_step, verifier


@data_source
def dummy_source(ctx, value=0):
    return ctx.get("replicate", 0) + value


@pipeline_step()
def add(data, ctx, inc=1):
    return data + inc


@pipeline_step()
def metrics_step(data, ctx):
    ctx.metrics.add("result", data)
    return {"result": data}


@verifier
def always_sig(baseline, treatment):
    return {"p_value": 0.01, "significant": True, "accepted": True}


def rank(res):
    return res["p_value"]


def inc(ctx, amount=1):
    ctx.add("val", amount)


@pytest.fixture()
def json_config(tmp_path: Path) -> Path:
    cfg = {
        "datasource": {"target": f"{__name__}.dummy_source", "params": {"value": 1}},
        "pipeline": [
            {"target": f"{__name__}.add", "params": {"inc": 1}},
            {"target": f"{__name__}.metrics_step"},
        ],
        "hypothesis": {
            "verifier": {"target": f"{__name__}.always_sig"},
            "ranker": f"{__name__}.rank",
            "metrics": "result",
        },
        "treatments": [
            {"name": "inc", "apply": {"target": f"{__name__}.inc", "params": {"amount": 1}}}
        ],
        "replicates": "2",
    }
    path = tmp_path / "conf.json"
    path.write_text(json.dumps(cfg))
    return path


def test_load_experiment_success(json_config: Path):
    exp = load_experiment_from_file(json_config)
    exp.validate()
    result = exp.run()
    assert result.metrics.baseline.metrics["result"] == [2, 3]
    assert result.metrics.treatments["inc"].metrics["result"] == [2, 3]


def test_load_experiment_invalid(tmp_path: Path):
    bad = tmp_path / "bad.json"
    bad.write_text("[]")
    with pytest.raises(ValueError):
        load_experiment_from_file(bad)


def test_load_valid_yaml_config():
    config = {
        "datasource": {"target": f"{__name__}.dummy_source", "params": {"value": 2}},
        "pipeline": [{"target": f"{__name__}.add"}],
        "hypothesis": {"verifier": {"target": f"{__name__}.always_sig"}, "ranker": f"{__name__}.rank", "metrics": "result"},
        "treatments": [
            {"name": "t", "apply": {"target": f"{__name__}.inc"}},
        ],
        "replicates": 2,
    }
    exp = load_experiment(config)
    assert exp.replicates == 2 and len(exp.treatments) == 1


def test_load_invalid_yaml_missing_section():
    config = {"replicates": 1}
    with pytest.raises(KeyError):
        load_experiment(config)


def test_load_yaml_type_conversion_error():
    config = {
        "datasource": {"target": f"{__name__}.dummy_source"},
        "pipeline": [{"target": f"{__name__}.add"}],
        "hypothesis": {"verifier": {"target": f"{__name__}.always_sig"}, "ranker": f"{__name__}.rank", "metrics": "result"},
        "replicates": "two",
    }
    with pytest.raises(ValueError):
        load_experiment(config)
