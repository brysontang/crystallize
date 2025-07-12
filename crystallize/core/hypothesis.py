from typing import Any, Callable, Dict, Mapping, Sequence, Optional

from crystallize.core.exceptions import MissingMetricError


class Hypothesis:
    """A quantifiable assertion to verify after experiment execution."""

    def __init__(
        self,
        verifier: Callable[[Mapping[str, Sequence[Any]], Mapping[str, Sequence[Any]]], Mapping[str, Any]],
        metrics: str | Sequence[str] | Sequence[Sequence[str]] | None = None,
        ranker: Callable[[Mapping[str, Any]], float] | None = None,
        name: Optional[str] = None,
    ) -> None:
        self.metrics_spec = metrics
        self.verifier = verifier
        self.ranker = ranker or (lambda res: float(res.get("p_value", 0.0)))
        if name:
            self.name = name
        elif hasattr(ranker, "__name__"):
            self.name = ranker.__name__  # type: ignore[arg-type]
        else:
            self.name = "hypothesis"

    # ---- public API -----------------------------------------------------

    def verify(
        self,
        baseline_metrics: Mapping[str, Sequence[Any]],
        treatment_metrics: Mapping[str, Sequence[Any]],
    ) -> Any:
        def subset(keys: Sequence[str]) -> tuple[Dict[str, Sequence[Any]], Dict[str, Sequence[Any]]]:
            b: Dict[str, Sequence[Any]] = {}
            t: Dict[str, Sequence[Any]] = {}
            for k in keys:
                try:
                    b[k] = baseline_metrics[k]
                    t[k] = treatment_metrics[k]
                except KeyError:
                    raise MissingMetricError(k)
            return b, t

        spec = self.metrics_spec
        if spec is None:
            groups = [list(baseline_metrics.keys())]
        elif isinstance(spec, str):
            groups = [[spec]]
        elif spec and isinstance(spec[0], Sequence) and not isinstance(spec[0], (str, bytes)):  # type: ignore[index]
            groups = [list(g) for g in spec]  # type: ignore[arg-type]
        else:
            groups = [list(spec)]  # type: ignore[arg-type]

        outputs = []
        for group in groups:
            b, t = subset(group)
            outputs.append(self.verifier(b, t))

        return outputs[0] if len(outputs) == 1 else outputs

    def rank_treatments(self, verifier_results: Mapping[str, Any]) -> Mapping[str, Any]:
        scores = {name: self.ranker(res) for name, res in verifier_results.items()}
        ranked = sorted(scores.items(), key=lambda x: x[1])
        best = ranked[0][0] if ranked else None
        return {"best": best, "ranked": ranked}
