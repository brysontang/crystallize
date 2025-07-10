from crystallize import (
    data_source,
    hypothesis,
    pipeline,
    pipeline_step,
    statistical_test,
    treatment,
)
from crystallize.core.context import FrozenContext
from crystallize.core.experiment import Experiment
from crystallize.core.pipeline_step import exit_step


@statistical_test
def always_significant(baseline, treatment, *, alpha: float = 0.05):
    return {"p_value": 0.01, "significant": True}


@data_source
def dummy_source(ctx: FrozenContext):
    return ctx.as_dict().get("increment", 0)


@pipeline_step()
def pass_step(data, ctx):
    return {"metric": data}


@pipeline_step()
def identity_step(data, ctx):
    return data


@treatment("treat")
def treat(ctx: FrozenContext) -> None:
    ctx.add("increment", 1)


if __name__ == "__main__":
    pipeline_obj = pipeline(exit_step(identity_step()), pass_step())
    datasource = dummy_source()
    hyp = hypothesis(
        metric="metric", direction="increase", statistical_test=always_significant()
    )
    treat_step = treat()

    experiment = (
        Experiment()
        .with_datasource(datasource)
        .with_pipeline(pipeline_obj)
        .with_treatments([treat_step])
        .with_hypotheses([hyp])
        .with_replicates(2)
    )
    experiment.validate()
    result = experiment.run()
    print(result.metrics)
    print(result.errors)
    print("apply baseline:", experiment.apply(data=5))
    print("apply treatment:", experiment.apply(treatment_name="treat", data=5))
