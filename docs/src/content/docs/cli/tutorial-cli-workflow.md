---
title: 'Tutorial: Your First CLI Experiment'
description: Launch, scaffold, run, and inspect an experiment with the Textual UI.
---

This tutorial guides you through the end-to-end CLI experience—scaffolding code, running it, and reading the results—all without leaving the terminal.

## 1. Launch the CLI

```bash
crystallize
```

You’ll land on the **selection screen**:

- Left pane: ASCII banner + tree of discovered experiments/graphs (grouped by `cli.group` in `config.yaml`).
- Right pane: Live `config.yaml` editor and metadata panel.
- Footer: Key bindings (`n` new, `r` refresh, `e` errors, `q` quit, `Enter` run).

## 2. Scaffold an Experiment

Press `n` to open **Create New Experiment**.

- Provide a lowercase name (`hello-crystallize`).
- Leave `steps.py`, `datasources.py`, `verifiers.py` selected; add `outputs.py` if you plan to declare artifacts.
- Toggle **Add example code** to populate the files with a runnable starter.
- Optionally enable **Use outputs from other experiments** to create a DAG node referencing upstream artifacts.
- Press **Create**. A new folder appears under `experiments/hello-crystallize/`.

## 3. Run It

Back on the selection screen:

1. Highlight the experiment (arrow keys).
2. The right panel shows a Markdown summary, estimated runtime (based on historic timings), and an editable config tree. Press `e` on a node to edit values in place.
3. Press `Enter` or click **Run**.

The **run screen** contains:

- Left sidebar – experiment tree and treatment tree. Use `l` to toggle caching for highlighted nodes and `x` to enable/disable treatments (state persists to `config.state.json`).
- Tabs – `Logs`, `Summary`, `Errors`. `t` flips between rich and plain-text output, `S` focuses the summary tab.
- `R` toggles **Run** ↔ **Cancel**. `e` opens the highlighted node in `$CRYSTALLIZE_EDITOR`, `$EDITOR`, or `$VISUAL`.
- The top bar shows active experiment, treatment, replicate progress, and ETA (computed via an exponential moving average).

## 4. Inspect the Summary

After the run completes, the summary tab lists:

- **Metrics** – baseline plus each treatment, including artifact version suffixes (`(v0)`).
- **Hypotheses** – verifier outputs (p-values, guardrail flags). The best treatment is highlighted according to the ranker.
- **Artifacts** – links to files saved by `ArtifactPlugin` (configured per experiment). Selecting a row and pressing `e` opens the artifact in your editor.

When caching is enabled, rerunning shows lock icons on cached steps and highlights “resume” mode in the header.

## 5. Iterate Quickly

- Edit `config.yaml` directly from the tree, or open `datasources.py`/`steps.py` in your editor; the CLI reloads modules before each run.
- Use `r` on the selection screen to pick up new experiments or changes to configs (useful when switching Git branches).
- Press `e` on the selection screen to view load errors; the modal includes the traceback so you can fix syntax errors without leaving the UI.

## 6. Next Steps

- Declare `outputs` and build DAGs; use `ExperimentGraph.from_yaml` to execute them programmatically or select the graph node in the CLI.
- Toggle treatments on and off to focus on promising variants. The persisted state file keeps your choices between runs.
- Enable artifact versioning (`ArtifactPlugin(versioned=True)`) to compare historical runs in the summary tab.
