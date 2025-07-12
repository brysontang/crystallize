from typing import Dict, List, Mapping

from crystallize import pipeline_step
from crystallize.core.context import FrozenContext


@pipeline_step()
def explained_variance(data: Mapping[str, List[float]], ctx: FrozenContext) -> Dict[str, float]:
    """Compute explained variance ratio from eigenvalues."""

    eigvals = data.get("eigenvalues", [])
    total = sum(eigvals)
    ratio = eigvals[0] / total if total else 0.0
    ctx.metrics.add("explained_variance", ratio)
    return {"explained_variance": ratio}
