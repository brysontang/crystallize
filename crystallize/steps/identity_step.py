from typing import Any
from crystallize.core.pipeline_step import PipelineStep
from crystallize.core.context import FrozenContext

class IdentityStep(PipelineStep):
    def __call__(self, data: Any, ctx: FrozenContext) -> Any:
        return data

    @property
    def params(self) -> dict:
        return {}
