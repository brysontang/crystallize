from crystallize import pipeline_step
from crystallize.utils.context import FrozenContext


@pipeline_step()
def add_one(data: int, ctx: FrozenContext) -> dict:
    ctx.metrics.add("val", data + 1)
    return {"val": data + 1}
