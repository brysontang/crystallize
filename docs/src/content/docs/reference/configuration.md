---
title: Configuration Reference
---

Single-source reference for `config.yaml` files used by the CLI and `Experiment.from_yaml`.

## Root Keys

| Key | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `name` | string | No | Folder name | Human-friendly experiment name shown in the CLI and used for artifact paths. |
| `description` | string | No | `""` | Freeform description surfaced in the CLI panels. |
| `replicates` | integer | No | `1` | Number of replicates to run for each condition. |
| `steps` | list | Yes | – | Ordered list of step factory names from `steps.py`. Entries can be strings or `{factory: {param: value}}` mappings. |
| `datasource` | mapping or list of mappings | Yes | – | Defines input aliases. Each alias maps to a factory in `datasources.py` or a DAG reference (see below). |
| `outputs` | mapping | No | `{}` | Declares artifacts and optional loaders/writers from `outputs.py`. |
| `treatments` | mapping | No | `{}` | Treatment name → parameter dict applied to the context. |
| `hypotheses` | list | No | `[]` | Hypothesis objects built from `verifiers.py` entries. |
| `cli` | mapping | No | `{}` | CLI metadata for grouping, icons, and ordering. |

## `cli` Section

| Key | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `group` | string | No | `"Graphs"` for DAGs, `"Experiments"` otherwise | Sidebar grouping label. |
| `priority` | integer | No | `999` | Sort order within a group (lower = higher). |
| `icon` | string (emoji/char) | No | `📈` for DAGs, `🧪` otherwise | Icon shown in the CLI tree. |
| `color` | string (hex) | No | `null` | Optional accent color for the CLI label. |
| `hidden` | boolean | No | `false` | If `true`, the experiment/graph is omitted from discovery. |

## `datasource` Section

Each entry maps an alias to one of:

- A factory name from `datasources.py`: `data: load_data`.
- A DAG reference to an upstream artifact: `summary: "experiment_a#summary"`.

Aliases defined as a list of single-item mappings are merged, which lets you spread datasource declarations across files when needed.

## `outputs` Section

Declare artifacts produced by steps so downstream nodes and the CLI know how to read/write them.

| Field | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `file_name` | string | No | Alias name | File name to write under the step directory. |
| `writer` | string | No | `null` | Function name in `outputs.py` that receives `(data, path)` and writes bytes. |
| `loader` | string | No | `null` | Function name in `outputs.py` that reads the artifact back in. |

Example:

```yaml
outputs:
  summary:
    file_name: summary.json
    writer: dump_json
    loader: load_json
```

## `treatments` Section

Map treatment names to context parameters. Treatments inherit by name in DAGs; downstream selections activate same-named upstream treatments automatically.

```yaml
treatments:
  high_lr:
    lr: 0.05
  dropout:
    rate: 0.2
```

## `hypotheses` Section

Each list item builds a `Hypothesis` using factories from `verifiers.py`.

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | Recommended | Display name for the hypothesis; defaults to the verifier/ranker name if omitted. |
| `verifier` | string | Yes | Factory name in `verifiers.py` that returns a verifier callable. |
| `metrics` | string or list | Yes | Metric key or keys to pass into the verifier (single string or list of groups). |

Example:

```yaml
hypotheses:
  - name: ttest_accuracy
    verifier: two_sample_ttest
    metrics: ["accuracy"]
```
