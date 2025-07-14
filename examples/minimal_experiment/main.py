# main.py
from crystallize import (
    data_source,
    hypothesis,
    pipeline_step,
    treatment,
    verifier,
)
from crystallize.core.plugins import LoggingPlugin
from crystallize.core.execution import ParallelExecution
from crystallize.core.experiment import Experiment
from crystallize.core.pipeline import Pipeline
from crystallize.core.context import FrozenContext
from scipy.stats import ttest_ind
import random
 
# 1. Define how to get data
@data_source
def initial_data(ctx: FrozenContext):
    return [0, 0, 0]

# 2. Define the data processing pipeline
@pipeline_step()
def add_delta(data, ctx: FrozenContext):
    # The 'delta' value is injected by our treatment
    return [x + ctx.get("delta", 0.0) for x in data]

@pipeline_step()
def add_random(data, ctx: FrozenContext):
    # Add some random noise to the data
    # This removes scipy's "catastrophic cancellation" error
    replicate = ctx.get('replicate', 0)
    treatment = ctx.get('condition', 'add_ten_treatment')
    return [x + random.random() for x in data]

@pipeline_step()
def compute_metrics(data, ctx: FrozenContext):
    # Record a simple metric for later verification
    ctx.metrics.add("result", sum(data))
    return data

# 3. Define the treatment (the change we are testing)
add_ten = treatment(
    name="add_ten_treatment",
    apply={"delta": 10.0} # This dict is added to the context
)

# 4. Define the hypothesis to verify
@verifier
def welch_t_test(baseline, treatment, alpha: float = 0.05):
    t_stat, p_value = ttest_ind(
        treatment["result"], baseline["result"], equal_var=False
    )
    return {"p_value": p_value, "significant": p_value < alpha}

@hypothesis(verifier=welch_t_test(), metrics="result")
def check_for_improvement(res):
    # The ranker function determines the "best" treatment.
    # Lower p-value is better.
    return res.get("p_value", 1.0)

# 5. Build and run the experiment
if __name__ == "__main__":
    experiment = Experiment(
        datasource=initial_data(),
        pipeline=Pipeline([add_delta(), add_random(), compute_metrics()]),
        treatments=[add_ten()],
        hypotheses=[check_for_improvement],
        replicates=20,
        plugins=[ParallelExecution(), LoggingPlugin(verbose=True, log_level="DEBUG")],
    )
    experiment.validate()
    result = experiment.run()

    # Print the results for our hypothesis
    hyp_result = result.get_hypothesis("check_for_improvement")
    print(hyp_result.results)
    print(result.print_tree())
