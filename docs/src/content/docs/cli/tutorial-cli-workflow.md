---
title: 'Tutorial: Your First CLI Experiment'
description: A complete, story-driven walkthrough of creating, configuring, and running an experiment from the command line.
---

Welcome! This tutorial is your first step into the world of Crystallize. We'll follow a common story: you have an idea for an experiment and want to see it working as quickly as possible. This guide will show you how to go from zero to a fully functional, running experiment in just a few commands, all from the interactive Command Line Interface (CLI).

## The Goal: A Zero-to-Hero Experiment

We're going to use Crystallize's scaffolding power to create a pre-built experiment, run it, and see real results immediately.

### Step 1: Scaffold a New Experiment with Examples

Instead of starting with empty files, we'll tell Crystallize to include example code for us.

1. From your terminal, launch the interactive TUI:
   ```bash
   crystallize
   ```
2. Press the <kbd>n</kbd> key to open the **Create New Experiment** screen.
3. Enter a name for your experiment, like `hello-crystallize`.
4. In the **Files to include** list, ensure the defaults (`steps.py`, `datasources.py`) are checked, and also check `verifiers.py`.
5. Crucially, check the **Add example code** box. This will populate our new files with runnable code.
6. Click **Create**.

Crystallize has just built a complete, working experiment in `experiments/hello-crystallize/`.

### Step 2: The First Run

Let's run our new experiment without any modifications.

1. Back on the main screen, your `hello-crystallize` experiment is highlighted. Press <kbd>Enter</kbd>.
2. The **Prepare Run** screen appears. Make sure only **datasource** and **steps** are enabled and select `rerun` to execute everything from scratch.
3. Press **Run** to start. The view switches to a live log, showing the pipeline for both the baseline and two example treatments. If something goes wrong while loading or running, the interface opens an **Errors** tab with the traceback so you can diagnose the issue. You can highlight any step in the tree and press <kbd>e</kbd> to open its source in your editor (set `$EDITOR`).

### Step 3: The Summary Tab – Instant Results!

After the run, the view switches to the **Summary** tab. Because we included example code, the summary is already populated with meaningful results. You'll see three main tables:

- **Metrics Table:** Shows the raw metrics collected during the run. The example code calculates a `val` metric, and you can see how its value differs between the baseline, `increase_by_one`, and `increase_by_two` treatments.
- **Artifacts Table:** Lists the artifacts saved during the run. Each cell links to the file produced by the corresponding treatment so you can open it directly.
- **Hypothesis Table:** Displays the results of the statistical test defined in the example. It compares each treatment to the baseline and reports a `p_value` and whether the result was significant.

Just by scaffolding and running, you've already got a complete experimental result!

### Step 4: Scaling Up with Replicates

A single run is great, but for statistical confidence we need more replicates.

1. Press <kbd>Esc</kbd> or <kbd>q</kbd> to exit the run screen and return to the main screen.
2. With `hello-crystallize` highlighted, look at the configuration tree on the right. This is a live editor for your `config.yaml`.
3. Use the arrow keys to navigate to `replicates`. Press <kbd>e</kbd> to edit, change the value from `1` to `10`, and press <kbd>Enter</kbd> to save.

### Step 5: The Second Run – More Power!

1. Press <kbd>Enter</kbd> on your experiment again.
2. Choose `rerun`.
3. The live runner now shows progress for all 10 replicates.
4. When the run completes, the **Summary** tab shows metrics from all 10 runs, giving you a much more robust statistical result for your hypotheses.

Congratulations! You've just seen the full power of the CLI workflow: scaffolding a working experiment, running it, and scaling it up for statistical significance, all in just a few minutes.
