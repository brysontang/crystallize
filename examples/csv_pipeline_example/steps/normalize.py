import statistics
from typing import List

from crystallize.core.context import FrozenContext
from crystallize.core.pipeline_step import PipelineStep


class NormalizeStep(PipelineStep):
    """Standardize columns to zero mean and unit variance."""

    def __call__(
        self, data: List[List[float]], ctx: FrozenContext
    ) -> List[List[float]]:
        if not data:
            return data
        columns = list(zip(*data))
        means = [statistics.mean(col) for col in columns]
        stdevs = [statistics.pstdev(col) or 1.0 for col in columns]
        normalized = [
            [(value - m) / s for value, m, s in zip(row, means, stdevs)] for row in data
        ]
        return normalized

    @property
    def params(self) -> dict:
        return {}
