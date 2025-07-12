import statistics
from typing import List

from crystallize import pipeline_step
from crystallize.core.context import FrozenContext


@pipeline_step()
def normalize(data: List[List[float]], ctx: FrozenContext) -> List[List[float]]:
    """Standardize columns to zero mean and unit variance."""

    if not data:
        return data
    columns = list(zip(*data))
    means = [statistics.mean(col) for col in columns]
    stdevs = [statistics.pstdev(col) or 1.0 for col in columns]
    normalized = [
        [(value - m) / s for value, m, s in zip(row, means, stdevs)] for row in data
    ]
    return normalized
