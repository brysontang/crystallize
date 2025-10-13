"""Plugins that persist provenance for agentic harness executions."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping

from crystallize.plugins.plugins import ArtifactPlugin, BasePlugin
from crystallize.utils.constants import BASELINE_CONDITION, CONDITION_KEY


def _json_default(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serialisable")


def _serialise(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return {k: _serialise(v) for k, v in value.items()}
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return [_serialise(v) for v in value]
    return value


class PromptProvenancePlugin(BasePlugin):
    """Collect and persist metadata about LLM prompt/response pairs."""

    def __init__(self, artifact_name: str = "llm_calls.json") -> None:
        self.artifact_name = artifact_name
        self._calls_by_condition: Dict[str, List[Mapping[str, Any]]] = {}
        self._seen_keys: set[str] = set()
        self._current_condition: str = BASELINE_CONDITION

    @property
    def calls_by_condition(self) -> Mapping[str, List[Mapping[str, Any]]]:
        return {k: list(v) for k, v in self._calls_by_condition.items()}

    def before_run(self, experiment) -> None:  # pragma: no cover - simple reset
        self._calls_by_condition.clear()

    def before_replicate(self, experiment, ctx) -> None:
        self._current_condition = ctx.get(CONDITION_KEY, BASELINE_CONDITION)
        self._seen_keys = set(ctx.as_dict().keys())

    def after_step(self, experiment, step, data, ctx) -> None:
        snapshot = ctx.as_dict()
        new_keys = [key for key in snapshot if key not in self._seen_keys and key.startswith("llm_call")]
        entries: List[Mapping[str, Any]] = []
        for key in new_keys:
            value = snapshot[key]
            if isinstance(value, Mapping):
                entries.append(dict(value))
            elif isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
                for item in value:
                    if isinstance(item, Mapping):
                        entries.append(dict(item))
        if entries:
            calls = self._calls_by_condition.setdefault(self._current_condition, [])
            calls.extend(entries)
        self._seen_keys.update(new_keys)

    def after_run(self, experiment, result) -> None:
        if not self._calls_by_condition:
            return
        artifact_plugin = experiment.get_plugin(ArtifactPlugin)
        if artifact_plugin is None:
            return
        base = (
            Path(artifact_plugin.root_dir)
            / (artifact_plugin.experiment_id)
            / f"v{artifact_plugin.version}"
        )
        for condition, calls in self._calls_by_condition.items():
            if not calls:
                continue
            dest = base / condition / "prompts"
            dest.mkdir(parents=True, exist_ok=True)
            with open(dest / self.artifact_name, "w", encoding="utf-8") as handle:
                json.dump(list(calls), handle, default=_json_default, indent=2, sort_keys=True)


class EvidenceBundlePlugin(BasePlugin):
    """Persist an evidence bundle linking claim, spec, code, tests and verdicts."""

    def __init__(self, filename: str = "bundle.json") -> None:
        self.filename = filename

    def after_run(self, experiment, result) -> None:
        artifact_plugin = experiment.get_plugin(ArtifactPlugin)
        if artifact_plugin is None:
            return
        base = (
            Path(artifact_plugin.root_dir)
            / (artifact_plugin.experiment_id)
            / f"v{artifact_plugin.version}"
        )
        prompt_plugin = experiment.get_plugin(PromptProvenancePlugin)
        prompt_calls = (
            prompt_plugin.calls_by_condition if prompt_plugin is not None else {}
        )
        provenance = result.provenance.get("ctx_changes", {})
        for condition, replicates in provenance.items():
            if condition == BASELINE_CONDITION:
                condition_metrics = result.metrics.baseline.metrics
            else:
                treatment_metrics = result.metrics.treatments.get(condition)
                condition_metrics = (
                    treatment_metrics.metrics if treatment_metrics else {}
                )
            bundle = self._build_bundle(
                condition,
                replicates,
                condition_metrics,
                result.metrics.hypotheses,
                prompt_calls.get(condition, []),
            )
            dest = base / condition / "evidence"
            dest.mkdir(parents=True, exist_ok=True)
            with open(dest / self.filename, "w", encoding="utf-8") as handle:
                json.dump(bundle, handle, default=_json_default, indent=2, sort_keys=True)

    def _build_bundle(
        self,
        condition: str,
        replicates: Mapping[int, List[Mapping[str, Any]]],
        metrics: Mapping[str, List[Any]],
        hypotheses,
        llm_calls: Iterable[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        claims: List[Any] = []
        specs: List[Any] = []
        code: List[Dict[str, Any]] = []
        runs: List[Dict[str, Any]] = []
        for rep, records in replicates.items():
            rep_outputs: MutableMapping[str, Any] = {}
            for record in records:
                wrote = record.get("ctx_changes", {}).get("wrote", {})
                if "claim" in wrote:
                    claims.append(_serialise(wrote["claim"].get("after")))
                if "spec" in wrote:
                    specs.append(_serialise(wrote["spec"].get("after")))
                if "generated_code" in wrote:
                    code.append(
                        {
                            "replicate": rep,
                            "source": wrote["generated_code"].get("after"),
                        }
                    )
                if "capsule_output" in wrote:
                    rep_outputs = wrote["capsule_output"].get("after", {})
            if rep_outputs:
                runs.append({"replicate": rep, "outputs": _serialise(rep_outputs)})
        bundle_claims = _dedupe_list(claims)
        bundle_specs = _dedupe_list(specs)
        verdicts: List[Dict[str, Any]] = []
        for hypothesis in hypotheses:
            result_for_condition = hypothesis.results.get(condition)
            if result_for_condition is None:
                continue
            verdicts.append(
                {
                    "hypothesis": hypothesis.name,
                    "result": _serialise(result_for_condition),
                    "ranking": _serialise(hypothesis.ranking),
                }
            )
        return {
            "condition": condition,
            "claims": bundle_claims,
            "specs": bundle_specs,
            "code": code,
            "runs": runs,
            "metrics": {key: list(values) for key, values in metrics.items()},
            "verdicts": verdicts,
            "llm_calls": list(llm_calls),
        }


def _dedupe_list(items: Iterable[Any]) -> List[Any]:
    seen: Dict[str, Any] = {}
    for item in items:
        serialised = json.dumps(_serialise(item), sort_keys=True)
        seen[serialised] = _serialise(item)
    return list(seen.values())
