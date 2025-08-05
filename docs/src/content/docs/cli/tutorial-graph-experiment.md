---
title: 'Putting It All Together - Building a Graph Experiment'
description: A guided walkthrough for constructing a small graph of experiments and consuming their outputs.
---

This tutorial walks through creating a three-experiment graph that demonstrates how Crystallize chains experiments together. We'll create two simple "producer" experiments and a "consumer" experiment that uses their outputs.

## The Goal: Calculate a Comfort Index

We'll combine temperature and humidity analyses, then test whether a scaling factor significantly changes the temperature average.

### Step 1: Create the `temperature-stats` Experiment

1. In the TUI, press <kbd>n</kbd> to create a new experiment named `temperature-stats`.
2. Ensure `datasources.py`, `steps.py`, `outputs.py`, and `verifiers.py` are included. Don't include the example files, then click `Create`.
3. In the config editor:
   - Under **outputs** add an output with alias `avg_temp_out` and file name `temp.json`.
   - Under **steps** add a step named `average_temp`.
   - Under **treatments** add a `baseline` treatment with `factor: 1.0` and another treatment `scaled_up` with `factor: 1.5`.
   - Under **hypotheses** add a hypothesis `check_scaling_effect` that uses the `t_test` verifier and checks the `average_temp` metric.
   - Set `replicates` to `30`.
4. Implement the logic in the generated Python files.

`experiments/temperature-stats/datasources.py`

```python
from crystallize import data_source
import random

@data_source
def temperatures(ctx):
    # Sample 2 random temperatures to introduce variability.
    # This is safe because Crystallize's SeedPlugin ensures that the random
    # seed is the same for the same replicate number across different
    # treatments, but different for each new replicate.
    all_temps = [72, 75, 71, 73, 76, 74, 70]
    return random.sample(all_temps, 2)
```

`experiments/temperature-stats/steps.py`

```python
from crystallize import pipeline_step, Artifact
import json

@pipeline_step()
def average_temp(data, *, avg_temp_out: Artifact, factor: float = 1.0):
    # The `factor` is injected by the treatment
    avg = (sum(data) / len(data)) * factor
    avg_temp_out.write(json.dumps({"average": avg}).encode())
    # Return the data and the metric for the hypothesis
    return data, {"average_temp": avg}
```

`experiments/temperature-stats/verifiers.py`

```python
from crystallize import verifier
from scipy.stats import ttest_ind

@verifier
def t_test(baseline_samples, treatment_samples):
    stat, p = ttest_ind(
        treatment_samples["average_temp"],
        baseline_samples["average_temp"],
        equal_var=False,
    )
    return {"p_value": p, "significant": p < 0.05}
```

Update `config.yaml` to use the new datasource function:

```yaml
datasource:
  temps: temperatures
```

### Step 2: Create the `humidity-stats` Experiment

1. Repeat the process for a new experiment named `humidity-stats`.
2. Include `outputs.py` and create an output `avg_humidity_out` with file name `humidity.json`.
3. Add a step `average_humidity` and set `replicates` to `1`.
4. Implement the step logic to compute a simple average using data such as `[0.45, 0.50, 0.55]`.

### Step 3: Create the `comfort-index` Experiment

1. Press <kbd>n</kbd> to create a new experiment named `comfort-index` and set `replicates` to `30`.
2. Check **Use outputs from other experiments** and select `avg_temp_out` from `temperature-stats` and `avg_humidity_out` from `humidity-stats`.
3. Add a final step named `calculate_comfort_index`.
4. Implement the step logic:

`experiments/comfort-index/steps.py`

```python
from crystallize import pipeline_step
import json

@pipeline_step()
def calculate_comfort_index(data: dict):
    with open(data["avg_temp_out"]) as f:
        temp = json.load(f)["average"]
    with open(data["avg_humidity_out"]) as f:
        humidity = json.load(f)["average"]
    comfort = temp - (humidity * 10)
    return data, {"comfort_index": comfort}
```

### Step 4: Run the Graph

When you run `comfort-index` in the TUI, Crystallize automatically executes its dependencies:

- `temperature-stats` runs for 30 replicates for both treatments.
- `humidity-stats` runs once.
- `comfort-index` runs 30 times, consuming the produced artifacts.

The summary shows metrics, artifacts, and hypothesis results for all experiments, demonstrating how graphs let you orchestrate complex workflows.
