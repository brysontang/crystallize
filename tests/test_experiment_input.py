from pathlib import Path

import pytest

from crystallize.datasources.artifacts import Artifact
from crystallize.datasources.datasource import ExperimentInput
from crystallize.utils.context import FrozenContext


class DummyArtifact(Artifact):
    def __init__(self, name: str, value: str, replicates: int | None) -> None:
        super().__init__(name, loader=lambda p: value)
        self.replicates = replicates

    def fetch(self, ctx: FrozenContext):  # type: ignore[override]
        return self.loader(Path())


def test_matching_replicates_sets_value() -> None:
    ds = ExperimentInput(
        a=DummyArtifact("a", "A", 2),
        b=DummyArtifact("b", "B", 2),
    )
    assert ds.replicates == 2


def test_mismatched_replicates_raise() -> None:
    with pytest.raises(ValueError, match="Conflicting replicates"):
        ExperimentInput(
            a=DummyArtifact("a", "A", 2),
            b=DummyArtifact("b", "B", 3),
        )
