from crystallize import pipeline_step, Artifact
from crystallize.utils.context import FrozenContext


@pipeline_step()
def add_one(
    data: int,
    ctx: FrozenContext,
    out: Artifact,
    *,
    delta: int = 1,
) -> dict:
    value = data + delta
    out.write(str(value).encode())
    ctx.metrics.add("val", value)
    return {"val": value}
