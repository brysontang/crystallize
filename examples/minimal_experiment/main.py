# main.py
from crystallize import (
    ExperimentBuilder,
    data_source,
    hypothesis,
    pipeline_step,
    treatment,
    from_scipy,
)
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
# Here, we use a helper to wrap a t-test from SciPy.
t_test_verifier = from_scipy(ttest_ind, alpha=0.05)

@hypothesis(verifier=t_test_verifier, metrics="result")
def check_for_improvement(res):
    # The ranker function determines the "best" treatment.
    # Lower p-value is better.
    return res.get("p_value", 1.0)

# 5. Build and run the experiment
if __name__ == "__main__":
    experiment = (
        ExperimentBuilder()
        .datasource(initial_data)
        .pipeline([add_delta, add_random, compute_metrics])
        .treatments([add_ten])
        .hypotheses([check_for_improvement])
        .replicates(20) # Run the experiment 20 times for statistical power
        .parallel(True) # Run replicates in parallel
        .build()
    )

    result = experiment.run()

    # Print the results for our hypothesis
    hyp_result = result.get_hypothesis("check_for_improvement")
    print(hyp_result.results)
