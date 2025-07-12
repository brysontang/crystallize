from crystallize import (
    data_source,
    hypothesis,
    pipeline_step,
    verifier,
    treatment,
)
from crystallize.core.builder import ExperimentBuilder
from crystallize.core.context import FrozenContext
from crystallize.core.pipeline_step import exit_step


@data_source
def dummy_source(ctx: FrozenContext):
    return ctx.get("delta", 0)


@pipeline_step(cacheable=False)
def pass_step(data, ctx):
    ctx.metrics.add("metric", data)
    return data


@pipeline_step(cacheable=False)
def delta_step(data, ctx):
    delta = ctx.get("delta", 0)
    return data + delta 


treat = treatment("treat", {"delta": 10})


@verifier
def always_significant(baseline, treatment, *, alpha: float = 0.05):
    # Simplified: Use built-ins, check mean increase
    treatment_mean = sum(treatment['metric']) / len(treatment)
    baseline_mean = sum(baseline['metric']) / len(baseline)
    return {"p_value": 0.01, "significant": treatment_mean > baseline_mean}


@hypothesis(verifier=always_significant(), metrics="metric")
def hyp(result):
    return result["p_value"]


if __name__ == "__main__":
    experiment = (
        ExperimentBuilder()
        .datasource(dummy_source)
        .pipeline([exit_step(delta_step), pass_step])
        .treatments([treat])
        .hypotheses([hyp])
        .replicates(2)
        .build()
    )

    result = experiment.run()
    print(result.metrics)
    print(result.errors)
    print("apply baseline:", experiment.apply(data=5))
    print("apply treatment:", experiment.apply(treatment_name="treat", data=5))