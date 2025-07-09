from typing import Dict, List, Mapping

from crystallize.core.context import FrozenContext
from crystallize.core.pipeline_step import PipelineStep


class ExplainedVarianceStep(PipelineStep):
    """Compute explained variance ratio from eigenvalues."""

    def __call__(
        self, data: Mapping[str, List[float]], ctx: FrozenContext
    ) -> Dict[str, float]:
        eigvals = data.get("eigenvalues", [])
        total = sum(eigvals)
        ratio = eigvals[0] / total if total else 0.0
        return {"explained_variance": ratio}

    @property
    def params(self) -> dict:
        return {}
