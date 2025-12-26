from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace

import pytest

from crystallize.agentic.schema import Claim, Spec
from crystallize.agentic.steps import (
    BoundedExecutionError,
    bounded_synthesis,
    execute_capsule,
    generate_spec,
    run_metamorphic_tests,
    specify_claim,
)
from crystallize.plugins.provenance import EvidenceBundlePlugin, PromptProvenancePlugin
from crystallize.plugins.plugins import ArtifactPlugin
from crystallize.utils.constants import BASELINE_CONDITION, CONDITION_KEY, REPLICATE_KEY
from crystallize.utils.context import FrozenContext
from crystallize.experiments.result import Result
from crystallize.experiments.result_structs import ExperimentMetrics, TreatmentMetrics


@pytest.fixture()
def frozen_ctx() -> FrozenContext:
    ctx = FrozenContext({CONDITION_KEY: BASELINE_CONDITION, REPLICATE_KEY: 0})
    return ctx


def test_specify_claim_adds_claim_to_context(frozen_ctx: FrozenContext) -> None:
    step = specify_claim(claim={"id": "c1", "text": "delta", "acceptance": {"rmse": 5}})
    (claim_obj, data), metadata = step("dataset", frozen_ctx)
    assert isinstance(claim_obj, Claim)
    assert frozen_ctx.get("claim").id == "c1"
    assert metadata["claim_id"] == "c1"
    assert data == "dataset"
    assert frozen_ctx.get("raw_data") == "dataset"


def test_generate_spec_uses_static_spec(frozen_ctx: FrozenContext) -> None:
    claim_step = specify_claim(claim={"id": "c2", "text": "spec", "acceptance": {}})
    claim_obj, _ = claim_step("raw", frozen_ctx)
    spec_step = generate_spec(spec=Spec(allowed_imports=["math"]))
    (claim, spec, raw), metadata = spec_step(claim_obj, frozen_ctx)
    assert claim.id == "c2"
    assert spec.allowed_imports == ["math"]
    loaded = json.loads(metadata["spec_json"])
    assert loaded["allowed_imports"] == ["math"]


def test_bounded_synthesis_validates_imports(frozen_ctx: FrozenContext) -> None:
    claim_step = specify_claim(claim={"id": "c3", "text": "bounded", "acceptance": {}})
    claim_data, _ = claim_step({}, frozen_ctx)
    spec_step = generate_spec(spec=Spec(allowed_imports=["math"]))
    spec_data, _ = spec_step(claim_data, frozen_ctx)
    synth_step = bounded_synthesis(
        code="""
import math

def fit_and_eval(data):
    return {"rmse": math.sqrt(sum(x * x for x in data))}
"""
    )
    (claim_obj, spec_obj, code_str, payload), metadata = synth_step(spec_data, frozen_ctx)
    assert "code_sha" in metadata
    assert "math" in code_str
    assert payload == {}
    bad_step = bounded_synthesis(
        code="""
import os

def fit_and_eval(data):
    return {"rmse": 1.0}
"""
    )
    with pytest.raises(BoundedExecutionError):
        bad_step(spec_data, frozen_ctx)


def test_bounded_synthesis_allows_from_imports(frozen_ctx: FrozenContext) -> None:
    claim_step = specify_claim(claim={"id": "c3a", "text": "bounded", "acceptance": {}})
    claim_data, _ = claim_step({}, frozen_ctx)
    spec_step = generate_spec(spec=Spec(allowed_imports=["sklearn.metrics"]))
    spec_data, _ = spec_step(claim_data, frozen_ctx)
    synth_step = bounded_synthesis(
        code="""
from sklearn.metrics import mean_squared_error

def fit_and_eval(data):
    return {"rmse": float(mean_squared_error([0], [0]))}
"""
    )
    synth_step(spec_data, frozen_ctx)


def test_bounded_synthesis_blocks_dunder_escalation(frozen_ctx: FrozenContext) -> None:
    claim_step = specify_claim(claim={"id": "c3b", "text": "bounded", "acceptance": {}})
    claim_data, _ = claim_step([], frozen_ctx)
    spec_step = generate_spec(spec=Spec(allowed_imports=[]))
    spec_data, _ = spec_step(claim_data, frozen_ctx)
    synth_step = bounded_synthesis(
        code="""
def fit_and_eval(data):
    return {"value": (1).__class__.__mro__}
"""
    )
    with pytest.raises(BoundedExecutionError):
        synth_step(spec_data, frozen_ctx)


def test_bounded_synthesis_rejects_async_entrypoint(frozen_ctx: FrozenContext) -> None:
    claim_step = specify_claim(claim={"id": "c3c", "text": "async", "acceptance": {}})
    claim_data, _ = claim_step([], frozen_ctx)
    spec_step = generate_spec(spec=Spec(allowed_imports=[]))
    spec_data, _ = spec_step(claim_data, frozen_ctx)
    synth_step = bounded_synthesis(
        code="""
async def fit_and_eval(data):
    return {"value": 1}
"""
    )
    with pytest.raises(BoundedExecutionError, match="must be a sync function"):
        synth_step(spec_data, frozen_ctx)


def test_execute_capsule_runs_code(frozen_ctx: FrozenContext) -> None:
    claim_step = specify_claim(claim={"id": "c4", "text": "capsule", "acceptance": {}})
    claim_data, _ = claim_step(3, frozen_ctx)
    spec_step = generate_spec(
        spec=Spec(allowed_imports=["math"], resources={"time_s": 2})
    )
    spec_data, _ = spec_step(claim_data, frozen_ctx)
    synth_step = bounded_synthesis(
        code="""
import math

def fit_and_eval(data):
    return {"rmse": float(math.sqrt(data))}
"""
    )
    exec_input, _ = synth_step(spec_data, frozen_ctx)
    exec_step = execute_capsule()
    (claim_obj, spec_obj, result), metadata = exec_step(exec_input, frozen_ctx)
    assert result["rmse"] == pytest.approx(math.sqrt(3), rel=1e-6)
    assert metadata["rmse"] == result["rmse"]


def test_execute_capsule_detects_runtime_imports(frozen_ctx: FrozenContext) -> None:
    claim_step = specify_claim(claim={"id": "c4a", "text": "capsule", "acceptance": {}})
    claim_data, _ = claim_step(None, frozen_ctx)
    spec = Spec(allowed_imports=["importlib"], resources={"time_s": 2})
    spec_step = generate_spec(spec=spec)
    spec_data, _ = spec_step(claim_data, frozen_ctx)
    synth_step = bounded_synthesis(
        code="""
import importlib

def fit_and_eval(data):
    importlib.import_module("os")
    return {"rmse": 1.0}
"""
    )
    exec_input, _ = synth_step(spec_data, frozen_ctx)
    exec_step = execute_capsule()
    with pytest.raises(BoundedExecutionError):
        exec_step(exec_input, frozen_ctx)


def test_run_metamorphic_tests_records_results(frozen_ctx: FrozenContext) -> None:
    claim_step = specify_claim(claim={"id": "c6", "text": "meta", "acceptance": {}})
    claim_data, _ = claim_step([1, 2, 3], frozen_ctx)
    spec = Spec(
        allowed_imports=[],
        properties=[{"name": "perm", "metamorphic": "permute_rows", "metric": "total"}],
    )
    spec_data, _ = generate_spec(spec=spec)(claim_data, frozen_ctx)
    synth_step = bounded_synthesis(
        code="""
def fit_and_eval(data):
    return {"total": sum(data)}
"""
    )
    exec_input, _ = synth_step(spec_data, frozen_ctx)
    exec_step = execute_capsule()
    execute_output, exec_metadata = exec_step(exec_input, frozen_ctx)
    assert exec_metadata["total"] == 6
    meta_step = run_metamorphic_tests()
    (_, _, metrics), meta_metadata = meta_step(execute_output, frozen_ctx)
    assert metrics["total"] == 6
    assert meta_metadata["perm_pass"] is True
    stored = frozen_ctx.get("metamorphic_perm_result")
    assert stored["transform"] == "permute_rows"
    assert stored["passed"] is True


def test_run_metamorphic_tests_flags_failures(frozen_ctx: FrozenContext) -> None:
    claim_step = specify_claim(claim={"id": "c7", "text": "meta", "acceptance": {}})
    claim_data, _ = claim_step([1, 2, 3], frozen_ctx)
    spec = Spec(
        allowed_imports=[],
        properties=[{"name": "first", "metamorphic": "permute_rows", "metric": "first"}],
    )
    spec_data, _ = generate_spec(spec=spec)(claim_data, frozen_ctx)
    synth_step = bounded_synthesis(
        code="""
def fit_and_eval(data):
    return {"first": data[0]}
"""
    )
    exec_input, _ = synth_step(spec_data, frozen_ctx)
    exec_step = execute_capsule()
    execute_output, _ = exec_step(exec_input, frozen_ctx)
    meta_step = run_metamorphic_tests()
    (_, _, _), meta_metadata = meta_step(execute_output, frozen_ctx)
    assert meta_metadata["first_pass"] is False


def test_run_metamorphic_tests_numeric_fallback(frozen_ctx: FrozenContext) -> None:
    payload = {"values": [1, 2, 3], "message": "base"}
    claim_step = specify_claim(claim={"id": "c7a", "text": "meta", "acceptance": {}})
    claim_data, _ = claim_step(payload, frozen_ctx)
    spec = Spec(
        allowed_imports=[],
        properties=[{"name": "message", "transform": "identity", "tolerance": 0.0}],
    )
    spec_data, _ = generate_spec(spec=spec)(claim_data, frozen_ctx)
    synth_step = bounded_synthesis(
        code="""
def fit_and_eval(data):
    total = sum(data["values"])
    return {"total": total, "message": data["message"]}
"""
    )
    exec_input, _ = synth_step(spec_data, frozen_ctx)
    exec_step = execute_capsule()
    execute_output, _ = exec_step(exec_input, frozen_ctx)

    def _override_identity(data):
        clone = {**data}
        clone["message"] = "transformed"
        return clone

    meta_step = run_metamorphic_tests(transforms={"identity": _override_identity})
    (_, _, _), meta_metadata = meta_step(execute_output, frozen_ctx)
    assert meta_metadata["message_pass"] is True
    stored = frozen_ctx.get("metamorphic_message_result")
    assert stored["metrics"]["message"] == "transformed"


def test_run_metamorphic_aligned_transform(frozen_ctx: FrozenContext) -> None:
    dataset = ([1, 2, 3], [4, 5, 6])
    claim_step = specify_claim(claim={"id": "c8", "text": "meta", "acceptance": {}})
    claim_data, _ = claim_step(dataset, frozen_ctx)
    spec = Spec(
        allowed_imports=[],
        properties=[{"name": "aligned", "metamorphic": "permute_rows_aligned", "metric": "first"}],
    )
    spec_data, _ = generate_spec(spec=spec)(claim_data, frozen_ctx)
    synth_step = bounded_synthesis(
        code="""
def fit_and_eval(data):
    x, y = data
    return {"first": (x[0], y[0])}
"""
    )
    exec_input, _ = synth_step(spec_data, frozen_ctx)
    exec_step = execute_capsule()
    execute_output, _ = exec_step(exec_input, frozen_ctx)
    meta_step = run_metamorphic_tests()
    (_, _, _), meta_metadata = meta_step(execute_output, frozen_ctx)
    assert meta_metadata["aligned_pass"] is False
    stored = frozen_ctx.get("metamorphic_aligned_result")
    assert stored["metrics"]["first"] == (3, 6)


def test_permute_rows_aligned_fallback_no_len() -> None:
    """Test _permute_rows_aligned falls back when first element has no len()."""
    from crystallize.agentic.steps import _permute_rows_aligned

    # Object without __len__ as first element triggers fallback to _permute_rows
    class NoLen:
        pass

    no_len_obj = NoLen()
    payload = (no_len_obj, [1, 2, 3])
    result = _permute_rows_aligned(payload)
    # Falls back to _permute_rows which processes each tuple element:
    # - NoLen object can't be sliced, returned unchanged
    # - List [1, 2, 3] gets reversed to [3, 2, 1]
    assert len(result) == 2
    assert isinstance(result[0], NoLen)  # NoLen object unchanged (can't be reversed)
    assert result[1] == [3, 2, 1]  # List gets reversed


def test_permute_rows_aligned_empty_first_element() -> None:
    """Test _permute_rows_aligned returns unchanged when first element is empty."""
    from crystallize.agentic.steps import _permute_rows_aligned

    # Empty first element (length == 0) returns payload unchanged
    payload = ([], [])
    result = _permute_rows_aligned(payload)
    assert result is payload  # Same object returned unchanged


def test_permute_rows_aligned_fallback_non_reconstructible_type() -> None:
    """Test _permute_rows_aligned uses list fallback for non-reconstructible types."""
    from crystallize.agentic.steps import _permute_rows_aligned

    # frozenset can be indexed but can't be reconstructed from a generator
    # Use a custom class that supports indexing but not reconstruction
    class IndexableButNotReconstructible:
        def __init__(self):
            self._data = [1, 2, 3]

        def __len__(self):
            return len(self._data)

        def __getitem__(self, idx):
            return self._data[idx]

    payload = (IndexableButNotReconstructible(), [4, 5, 6])
    result = _permute_rows_aligned(payload)
    # First item should become a list (fallback), second stays as list
    assert result[0] == [3, 2, 1]
    assert result[1] == [6, 5, 4]


def test_permute_rows_aligned_fallback_non_indexable() -> None:
    """Test _permute_rows_aligned leaves non-indexable items unchanged."""
    from crystallize.agentic.steps import _permute_rows_aligned

    # Object that has len but can't be indexed
    class HasLenButNoIndex:
        def __len__(self):
            return 3

    item = HasLenButNoIndex()
    payload = ([1, 2, 3], item)
    result = _permute_rows_aligned(payload)
    # First item reversed, second item unchanged (same object)
    assert result[0] == [3, 2, 1]
    assert result[1] is item


@pytest.mark.parametrize("prompt_keys", [["llm_call_custom"], ["llm_call_a", "llm_call_b"]])
def test_prompt_provenance_collects_calls(frozen_ctx: FrozenContext, tmp_path: Path, prompt_keys: list[str]) -> None:
    plugin = PromptProvenancePlugin()
    artifact = ArtifactPlugin(root_dir=str(tmp_path), versioned=False)

    class DummyExperiment:
        def __init__(self) -> None:
            self.plugins = [artifact, plugin]
            self.name = "exp"
            self.id = "exp"

        def get_plugin(self, plugin_type):
            for plug in self.plugins:
                if isinstance(plug, plugin_type):
                    return plug
            return None

    experiment = DummyExperiment()
    artifact.before_run(experiment)
    plugin.before_run(experiment)
    plugin.before_replicate(experiment, frozen_ctx)
    for idx, key in enumerate(prompt_keys):
        frozen_ctx.add(key, {"model": "gpt", "prompt": f"p{idx}", "completion_sha": str(idx)})
        plugin.after_step(experiment, SimpleNamespace(), None, frozen_ctx)
    result = Result(
        metrics=ExperimentMetrics(
            baseline=TreatmentMetrics(metrics={}),
            treatments={},
            hypotheses=[],
        )
    )
    plugin.after_run(experiment, result)
    saved = next((tmp_path / "exp" / "v0" / BASELINE_CONDITION / "prompts").glob("*.json"))
    content = json.loads(saved.read_text())
    assert len(content) == len(prompt_keys)


def test_evidence_bundle_persists_summary(frozen_ctx: FrozenContext, tmp_path: Path) -> None:
    plugin = EvidenceBundlePlugin()
    artifact = ArtifactPlugin(root_dir=str(tmp_path), versioned=False)

    class DummyExperiment:
        def __init__(self) -> None:
            self.plugins = [artifact, plugin]
            self.name = "exp"
            self.id = "exp"

        def get_plugin(self, plugin_type):
            for plug in self.plugins:
                if isinstance(plug, plugin_type):
                    return plug
            return None

    experiment = DummyExperiment()
    artifact.before_run(experiment)
    claim = Claim(id="c5", text="claim", acceptance={})
    spec = Spec(allowed_imports=["math"])
    provenance = {
        BASELINE_CONDITION: {
            0: [
                {
                    "ctx_changes": {
                        "wrote": {
                            "claim": {"after": claim},
                            "spec": {"after": spec},
                            "generated_code": {"after": "def fit_and_eval(data): return {'rmse': 1}"},
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
    plugin.after_run(experiment, result)
    bundle_path = (
        tmp_path
        / "exp"
        / "v0"
        / BASELINE_CONDITION
        / "evidence"
        / "bundle.json"
    )
    assert bundle_path.exists()
    content = json.loads(bundle_path.read_text())
    assert content["claims"][0]["id"] == "c5"
    assert content["specs"][0]["allowed_imports"] == ["math"]
    assert content["runs"][0]["outputs"]["rmse"] == 1.0


def test_metamorphic_verifier_all_pass() -> None:
    """Test metamorphic verifier when all properties pass."""
    from crystallize.agentic.verifiers import metamorphic

    verifier_fn = metamorphic()  # Factory returns callable
    baseline = {}
    treatment = {"perm_pass": [True, True], "align_pass": [True, True]}
    result = verifier_fn(baseline, treatment)
    assert result["metamorphic_ok"] is True
    assert result["perm_pass"] is True
    assert result["align_pass"] is True


def test_metamorphic_verifier_some_fail() -> None:
    """Test metamorphic verifier when some properties fail."""
    from crystallize.agentic.verifiers import metamorphic

    verifier_fn = metamorphic()
    baseline = {}
    treatment = {"perm_pass": [True, False], "align_pass": [True, True]}
    result = verifier_fn(baseline, treatment)
    assert result["metamorphic_ok"] is False
    assert result["perm_pass"] is False
    assert result["align_pass"] is True


def test_metamorphic_verifier_no_properties() -> None:
    """Test metamorphic verifier with no properties."""
    from crystallize.agentic.verifiers import metamorphic

    verifier_fn = metamorphic()
    baseline = {}
    treatment = {"some_metric": [1, 2, 3]}  # No _pass keys
    result = verifier_fn(baseline, treatment)
    assert result["metamorphic_ok"] is True  # No properties = ok


def test_meets_claim_verifier_improvement() -> None:
    """Test meets_claim verifier with improvement."""
    from crystallize.agentic.verifiers import meets_claim

    verifier_fn = meets_claim(min_pct=10.0)
    baseline = {"rmse": [1.0, 1.0, 1.0]}
    treatment = {"rmse": [0.8, 0.8, 0.8]}  # 20% improvement
    result = verifier_fn(baseline, treatment)
    assert result["meets_claim"] is True
    assert result["pct_improvement"] == pytest.approx(20.0)
    assert result["p_value"] == pytest.approx(0.8)


def test_meets_claim_verifier_no_improvement() -> None:
    """Test meets_claim verifier with no improvement."""
    from crystallize.agentic.verifiers import meets_claim

    verifier_fn = meets_claim(min_pct=5.0)
    baseline = {"rmse": [1.0, 1.0, 1.0]}
    treatment = {"rmse": [1.0, 1.0, 1.0]}  # No improvement
    result = verifier_fn(baseline, treatment)
    assert result["meets_claim"] is False
    assert result["pct_improvement"] == pytest.approx(0.0)


def test_meets_claim_verifier_no_baseline() -> None:
    """Test meets_claim verifier with no baseline values."""
    from crystallize.agentic.verifiers import meets_claim

    verifier_fn = meets_claim()
    baseline = {}  # No rmse key
    treatment = {"rmse": [0.5]}
    result = verifier_fn(baseline, treatment)
    assert result["meets_claim"] is False
    assert result["pct_improvement"] == 0.0
    assert result["p_value"] == 1.0


def test_meets_claim_verifier_no_treatment() -> None:
    """Test meets_claim verifier with no treatment values."""
    from crystallize.agentic.verifiers import meets_claim

    verifier_fn = meets_claim()
    baseline = {"rmse": [1.0, 1.0]}
    treatment = {}  # No rmse key
    result = verifier_fn(baseline, treatment)
    # Treatment mean defaults to baseline mean, so 0% improvement
    assert result["meets_claim"] is False
    assert result["pct_improvement"] == pytest.approx(0.0)


def test_evidence_bundle_handles_numpy_types(frozen_ctx: FrozenContext, tmp_path: Path) -> None:
    np = pytest.importorskip("numpy")
    plugin = EvidenceBundlePlugin()
    artifact = ArtifactPlugin(root_dir=str(tmp_path), versioned=False)

    class DummyExperiment:
        def __init__(self) -> None:
            self.plugins = [artifact, plugin]
            self.name = "exp"
            self.id = "exp"

        def get_plugin(self, plugin_type):
            for plug in self.plugins:
                if isinstance(plug, plugin_type):
                    return plug
            return None

    experiment = DummyExperiment()
    artifact.before_run(experiment)

    claim = Claim(id="c_numpy", text="claim", acceptance={})
    spec = Spec(allowed_imports=["math"])
    provenance = {
        BASELINE_CONDITION: {
            0: [
                {
                    "ctx_changes": {
                        "wrote": {
                            "claim": {"after": claim},
                            "spec": {"after": spec},
                            "generated_code": {"after": "def f(): pass"},
                            "capsule_output": {
                                "after": {
                                    "rmse": np.float64(1.0),
                                    "curve": np.array([0.1, 0.2]),
                                }
                            },
                        }
                    }
                }
            ]
        }
    }
    result = Result(
        metrics=ExperimentMetrics(
            baseline=TreatmentMetrics(metrics={"rmse": [np.float64(1.0)]}),
            treatments={},
            hypotheses=[],
        ),
        provenance={"ctx_changes": provenance},
    )
    plugin.after_run(experiment, result)

    bundle_path = (
        tmp_path
        / "exp"
        / "v0"
        / BASELINE_CONDITION
        / "evidence"
        / "bundle.json"
    )
    assert bundle_path.exists()
    content = json.loads(bundle_path.read_text())
    assert content["metrics"]["rmse"] == [1.0]
    outputs = content["runs"][0]["outputs"]
    assert outputs["rmse"] == 1.0
    assert outputs["curve"] == pytest.approx([0.1, 0.2])
