from crystallize import (
    data_source,
    hypothesis,
    pipeline_step,
    statistical_test,
    treatment,
)
from crystallize.core.builder import ExperimentBuilder
from crystallize.core.context import FrozenContext
from crystallize.core.pipeline_step import exit_step


@statistical_test
def always_significant(baseline, treatment, *, alpha: float = 0.05):
    # Simplified: Use built-ins, check mean increase
    treatment_mean = sum(treatment) / len(treatment)
    baseline_mean = sum(baseline) / len(baseline)
    return {"p_value": 0.01, "significant": treatment_mean > baseline_mean}


@data_source
def dummy_source(ctx: FrozenContext):
    return ctx.get("delta", 0)  # Align key with treatment


@pipeline_step()
def pass_step(data, ctx):
    return {"metric": data}


@pipeline_step()
def delta_step(data, ctx):
    delta = ctx.get("delta", 0)
    return data + delta  # Simplified: Always add (no direction)


@treatment("treat")
def treat(ctx: FrozenContext) -> None:
    ctx.add("delta", 10)


if __name__ == "__main__":
    hyp = hypothesis(
        metric="metric", statistical_test=always_significant()
    )
    treat_step = treat()

    experiment = (
        ExperimentBuilder()
        .datasource(dummy_source)
        .pipeline([exit_step(delta_step), pass_step])
        .treatments([treat_step])
        .hypotheses([hyp])
        .replicates(2)
        .build()
    )
    result = experiment.run()
    print(result.metrics)
    print(result.errors)
    print("apply baseline:", experiment.apply(data=5))
    print("apply treatment:", experiment.apply(treatment_name="treat", data=5))