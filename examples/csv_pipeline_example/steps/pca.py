import math
import statistics
from typing import Dict, List

from crystallize import pipeline_step
from crystallize.core.context import FrozenContext


@pipeline_step()
def pca(data: List[List[float]], ctx: FrozenContext) -> Dict[str, List[float]]:
    """PCA for 2D data using eigen decomposition."""

    if not data:
        return {"eigenvalues": []}
    if len(data[0]) != 2:
        raise ValueError("PCAStep supports exactly 2 features for this example")
    xs, ys = zip(*data)
    mx, my = statistics.mean(xs), statistics.mean(ys)
    var_x = statistics.pvariance(xs)
    var_y = statistics.pvariance(ys)
    cov_xy = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / len(data)
    trace = var_x + var_y
    det = var_x * var_y - cov_xy**2
    lambda1 = trace / 2 + math.sqrt((trace / 2) ** 2 - det)
    lambda2 = trace - lambda1
    return {"eigenvalues": [lambda1, lambda2]}
