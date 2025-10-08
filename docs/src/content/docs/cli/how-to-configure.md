---
title: "How-To: Configure Experiments (config.yaml)"
description: Understand every field in a folder-based experiment.
---

Crystallize discovers experiments by scanning for `config.yaml`. Each folder typically includes `datasources.py`, `steps.py`, `outputs.py`, and `verifiers.py`. The YAML file stitches them together.

## 1. Top-Level Fields

```yaml
name: my-experiment          # optional – defaults to folder name
replicates: 12               # applies to baseline + each treatment (default: 1)
description: "Short blurb shown in the CLI details panel"
```

## 2. CLI Metadata

Controls how the experiment appears in the Textual UI.

```yaml
cli:
  group: Feature Experiments     # sidebar group
  priority: 10                   # lower numbers sorted first
  icon: "🧪"                      # emoji shown next to the label
  color: "#85C1E9"               # optional hex colour for the label
  hidden: false                  # skip discovery when true
```

## 3. Datasource

Map aliases to factories defined in `datasources.py` or to outputs from upstream experiments.

```yaml
datasource:
  raw: load_csv                  # loads via @data_source in datasources.py
  features: feature_experiment#embeddings   # consumes another experiment’s output
```

- When referencing another experiment (`experiment_name#output_name`), the loader instantiates an `Artifact`. The downstream pipeline receives the return value of the artifact’s loader function. By default that is `Path.read_bytes()`, so override `outputs.*.loader` to decode bytes into richer objects.
- If you provide a list of mappings instead of a dict, Crystallize merges them (useful when order matters).

## 4. Steps

Ordered list of pipeline factories defined in `steps.py`.

```yaml
steps:
  - load_dataframe
  - { clean_columns: { drop_nulls: true } }
  - train_model
```

- Strings call the matching factory with no arguments.
- Dictionaries let you pass keyword arguments (`{factory: {param: value}}`). Parameters flow into the decorated function and still support context injection.
- A step returning `(data, metrics_dict)` records metrics without mutating the context.

## 5. Outputs

Declare artifacts produced by the pipeline. Each entry becomes an `Artifact` instance.

```yaml
outputs:
  model_blob:
    file_name: model.pkl          # optional – defaults to alias
    writer: dump_pickle           # function in outputs.py
    loader: load_pickle           # used when another experiment consumes it
```

Pipeline steps accept these artifacts by annotating a parameter with `Artifact`:

```python
from crystallize import pipeline_step, Artifact

@pipeline_step()
def save_model(data, *, model_blob: Artifact):
    model_blob.write(data["model_bytes"])
    return data
```

Artifacts are written under `data/<experiment>/vN/...` by the default `ArtifactPlugin`. Enable `versioned: true` on the plugin to retain multiple runs.

## 6. Treatments

Context changes evaluated against the baseline.

```yaml
treatments:
  baseline: {}
  tuned_lr:
    learning_rate: 0.05
  temperature_sweep:
    temperature: 0.9
```

- Keys become treatment names in the CLI and result summaries.
- Values merge into the context. Use nested dictionaries if you want to group related parameters.

## 7. Hypotheses

Hook verifiers defined in `verifiers.py`.

```yaml
hypotheses:
  - name: significance_check
    verifier: welch_t_test        # function wrapped with @verifier
    metrics: total_reward         # string, list, or nested lists
```

- Metrics refer to keys recorded with `ctx.metrics.add` or returned in `(data, metrics_dict)`.
- You can include multiple hypotheses; each runs independently after all replicates finish.

## 8. Putting It Together

Minimal example (`examples/yaml_experiment/config.yaml`):

```yaml
name: yaml-demo
replicates: 8
cli:
  group: Demo
  priority: 5
  icon: "🧪"
datasource:
  numbers: load_numbers
steps:
  - add_delta
  - record_total
outputs:
  total_blob:
    file_name: total.json
treatments:
  baseline: {}
  plus_one:
    delta: 1
hypotheses:
  - name: better_than_baseline
    verifier: welch_t_test
    metrics: total
```

## 9. Tips

- The CLI writes per-experiment state to `config.state.json` (inactive treatments, cache toggles). Check that file into git if you want to share defaults.
- Use `!include` or YAML anchors if you need to reuse fragments, but keep in mind the loader runs with standard `yaml.safe_load`.
- For DAGs, consider adding a `description:` to each node so the selection screen shows helpful detail.
