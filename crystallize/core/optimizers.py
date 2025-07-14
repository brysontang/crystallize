from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Union

from crystallize.core.treatment import Treatment


@dataclass
class Objective:
    """Defines the optimization goal."""

    metric: Union[str, List[str]]
    direction: Union[str, List[str]]


class BaseOptimizer(ABC):
    """The abstract base class for all optimization strategies."""

    def __init__(self, objective: Objective):
        self.objective = objective

    @abstractmethod
    def ask(self) -> list[Treatment]:
        """Suggest one or more Treatments for the next trial."""
        raise NotImplementedError

    @abstractmethod
    def tell(self, objective_values: dict[str, float]) -> None:
        """Provide the aggregated objective value(s) for the last trial."""
        raise NotImplementedError

    @abstractmethod
    def get_best_treatment(self) -> Treatment:
        """Return the best treatment found after all trials."""
        raise NotImplementedError

