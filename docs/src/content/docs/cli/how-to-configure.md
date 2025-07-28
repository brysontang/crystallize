---
title: "How-To: Configure Experiments (config.yaml)"
description: A detailed reference guide for every section of the experiment config.yaml file.
---

The `config.yaml` file is the heart of any Crystallize experiment managed via the CLI. It's a declarative blueprint that tells the framework how to construct and run your experiment. This guide serves as a reference for each section of the file.

## Anatomy of `config.yaml`

A complete `config.yaml` is composed of several key sections. While not all are required for every experiment, they provide a powerful way to define your entire workflow.

```yaml
# Top-level settings
name: my-experiment
replicates: 10

# CLI display settings
cli:
  group: My Experiments
  priority: 1
  icon: "🧪"

# Data input definitions
datasource:
  # ...

# The processing pipeline
steps:
  # ...

# Named file outputs
outputs:
  # ...

# Experimental variations
treatments:
  # ...

# Statistical tests
hypotheses:
  # ...
```

### Top-Level Settings
These define the fundamental properties of your experiment.
- `name` *(string)*: The unique identifier for the experiment. If not provided, the folder name is used.
- `replicates` *(integer)*: The number of times to run the pipeline for the baseline and each treatment. Defaults to `1`.

```yaml
name: titanic-age-analysis
replicates: 20
```

### `cli`
This section controls how your experiment appears in the interactive TUI.
- `group` *(string)*: The name of the collapsible group this experiment appears under.
- `priority` *(integer)*: A number used for sorting experiments within a group (lower numbers appear first).
- `icon` *(string)*: An emoji or character displayed next to the experiment name.
- `color` *(string, optional)*: A hex color code (e.g., "#85C1E9") to style the experiment's label.
- `hidden` *(boolean)*: If `true`, the experiment will not be discovered by the CLI.

```yaml
cli:
  group: Data Preprocessing
  priority: 5
  icon: "📊"
  color: "#85C1E9"
```

### `datasource`
Defines the input data for your pipeline. The structure depends on whether you are running a standard experiment or a graph that consumes artifacts from another experiment.

**Standard Experiment**: A dictionary mapping a key to the name of a `@data_source` function in your `datasources.py` file.
```yaml
# Fetches data using the `titanic_ages` function in `datasources.py`
datasource:
  ages: titanic_ages
```

**Graph Experiment**: A dictionary mapping a key to a special `experiment_name#output_name` string. This tells Crystallize to use an artifact from another experiment as input.
```yaml
# Uses the 'out' artifact from the 'test' experiment as input
datasource:
  in: test#out
```

### `steps`
A list defining the sequence of operations in your pipeline. Each item maps to a `@pipeline_step` function in your `steps.py` file.

```yaml
steps:
  - calculate_mean_age
  - normalize_data
```

A step can optionally return a tuple `(data, metrics_dict)` to record metrics. The first element is the data passed to the next step, and the second is a dictionary of metrics that will be available for hypotheses.

```python
# In steps.py
@pipeline_step()
def calculate_mean_age(data: pd.DataFrame):
    mean_age = data['Age'].mean()
    return data, {"mean_age": mean_age}
```

### `outputs`
A dictionary defining named file artifacts that your steps can write to. This is necessary for experiments that produce files to be consumed by other experiments in a graph.

To use an output, a pipeline step's function signature must include a parameter that has the same name as the output's alias and is type-hinted as `Artifact`.

```yaml
outputs:
  model_file:
    file_name: model.pkl
```

```python
# In steps.py, the parameter `model_file` matches the alias
from crystallize import pipeline_step, Artifact

@pipeline_step()
def train_model(data, *, model_file: Artifact):
    model = ...  # train your model
    model_file.write(model)  # Saves the model
    return data
```

#### Consuming Artifacts in Another Experiment
When another experiment uses this output via the datasource graph syntax, the data passed to its first step will be a dictionary mapping the datasource key to the artifact's file path.

```yaml
# In consumer-experiment/config.yaml
name: consumer-experiment
datasource:
  trained_model: producer-experiment#model_file
steps:
  - evaluate_model
```

```python
# In consumer-experiment/steps.py
from pathlib import Path
import pickle

@pipeline_step()
def evaluate_model(data: dict):
    model_path = data['trained_model']
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return ...
```

### `treatments`
Defines the experimental variations to test against the baseline. The values provided here are injected directly as parameters into your pipeline steps.

```yaml
treatments:
  baseline:
    delta: 0
  add_two:
    delta: 2
```

```python
@pipeline_step()
def add_delta(data, *, delta: int = 0):
    return [x + delta for x in data]
```

### `hypotheses`
A list of statistical tests to run on the collected metrics after all replicates are complete.

```yaml
hypotheses:
  - name: check_mean_difference
    verifier: welch_t_test
    metrics: mean_age
```

```python
from crystallize import verifier
from scipy.stats import ttest_ind

@verifier
def welch_t_test(baseline_samples, treatment_samples, alpha: float = 0.05):
    stat, p = ttest_ind(
        treatment_samples['mean_age'],
        baseline_samples['mean_age'],
        equal_var=False
    )
    return {"p_value": p, "significant": p < alpha}
```
