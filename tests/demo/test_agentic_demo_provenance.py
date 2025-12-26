from __future__ import annotations

import json
import os
from types import SimpleNamespace

import pytest

from crystallize.agentic.schema import Claim, Spec
from crystallize.agentic.steps import record_llm_call
from crystallize.plugins.provenance import EvidenceBundlePlugin, PromptProvenancePlugin
from crystallize.plugins.plugins import ArtifactPlugin
from crystallize.experiments.result import Result
from crystallize.experiments.result_structs import ExperimentMetrics, TreatmentMetrics
from crystallize.utils.constants import BASELINE_CONDITION, CONDITION_KEY, REPLICATE_KEY
from crystallize.utils.context import FrozenContext

pytestmark = [
    pytest.mark.demo,
    pytest.mark.skipif(
        os.getenv("RUN_DEMOS") != "1", reason="Demo tests are opt-in (RUN_DEMOS=1)."
    ),
]


@pytest.fixture()
def frozen_ctx() -> FrozenContext:
    return FrozenContext({CONDITION_KEY: BASELINE_CONDITION, REPLICATE_KEY: 0})


def test_demo_provenance_bundle(tmp_path, frozen_ctx: FrozenContext) -> None:
    artifact = ArtifactPlugin(root_dir=str(tmp_path), versioned=False)
    prompt_plugin = PromptProvenancePlugin()
    evidence_plugin = EvidenceBundlePlugin()

    class DummyExperiment:
        def __init__(self) -> None:
            self.plugins = [artifact, prompt_plugin, evidence_plugin]
            self.name = "demo-agentic"
            self.id = "demo-agentic"

        def get_plugin(self, plugin_type):
            for plugin in self.plugins:
                if isinstance(plugin, plugin_type):
                    return plugin
            return None

    experiment = DummyExperiment()
    artifact.before_run(experiment)
    prompt_plugin.before_run(experiment)
    prompt_plugin.before_replicate(experiment, frozen_ctx)

    record_llm_call(
        frozen_ctx, {"model": "demo", "prompt": "claim synthesis", "completion": "ok"}
    )
    prompt_plugin.after_step(experiment, SimpleNamespace(name="specify_claim"), None, frozen_ctx)
    record_llm_call(
        frozen_ctx, {"model": "demo", "prompt": "code synthesis", "completion": "ok"}
    )
    prompt_plugin.after_step(
        experiment, SimpleNamespace(name="bounded_synthesis"), None, frozen_ctx
    )

    claim = Claim(id="demo3", text="bundle provenance for harness", acceptance={})
    spec = Spec(allowed_imports=["math"])
    provenance = {
        BASELINE_CONDITION: {
            0: [
                {
                    "ctx_changes": {
                        "wrote": {
                            "claim": {"after": claim},
                            "spec": {"after": spec},
                            "generated_code": {
                                "after": "def fit_and_eval(data):\n    return {'rmse': 1.0}"
                            },
                            "capsule_output": {"after": {"rmse": 1.0}},
                        }
                    }
                }
            ]
        }
    }
    result = Result(
        metrics=ExperimentMetrics(
            baseline=TreatmentMetrics(metrics={"rmse": [1.0]}),
            treatments={},
            hypotheses=[],
        ),
        provenance={"ctx_changes": provenance},
    )

    prompt_plugin.after_run(experiment, result)
    evidence_plugin.after_run(experiment, result)

    base = tmp_path / "demo-agentic" / "v0" / BASELINE_CONDITION
    prompts_path = base / "prompts" / "llm_calls.json"
    assert prompts_path.exists()
    prompts_content = json.loads(prompts_path.read_text())
    assert len(prompts_content) == 2
    assert {entry["prompt"] for entry in prompts_content} == {
        "claim synthesis",
        "code synthesis",
    }

    bundle_path = base / "evidence" / "bundle.json"
    assert bundle_path.exists()
    bundle_content = json.loads(bundle_path.read_text())
    assert bundle_content["claims"][0]["id"] == "demo3"
    assert bundle_content["specs"][0]["allowed_imports"] == ["math"]
    assert bundle_content["code"][0]["source"].startswith("def fit_and_eval")
    assert bundle_content["runs"][0]["outputs"]["rmse"] == 1.0
    assert bundle_content["metrics"]["rmse"] == [1.0]
    assert len(bundle_content["llm_calls"]) == 2

