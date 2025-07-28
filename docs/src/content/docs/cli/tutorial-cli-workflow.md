---
title: "Tutorial: Your First CLI Experiment"
description: A complete walkthrough of creating, configuring, and running an experiment from the command line.
---

Welcome! This tutorial will guide you through the recommended workflow for using Crystallize: the interactive Command Line Interface (CLI). We'll build a complete experiment from scratch without writing boilerplate code, letting the TUI do the heavy lifting.

### Step 1: Scaffold a New Experiment 🏗️

First, let's create the file structure for our experiment.

1.  Launch the interactive TUI from your terminal:
    ```bash
    crystallize
    ```
2.  From the main selection screen, press the <kbd>n</kbd> key.
3.  This opens the **Create New Experiment** screen. Give your experiment a name (e.g., `my-cli-experiment`), ensure the default files are selected, and press the "Create" button.

Crystallize will generate a new folder at `experiments/my-cli-experiment/` containing a default `config.yaml` and the necessary Python files (`steps.py`, `datasources.py`, etc.).

### Step 2: Interactive Configuration ✍️

The TUI makes editing your experiment's configuration simple.

1.  **Select Your Experiment:** The main screen will now show `my-cli-experiment`. As it's highlighted, the right-hand panel displays its configuration in a live tree editor.
2.  **Add a New Step:** Let's add a new processing step to the pipeline.
    * Use the arrow keys to navigate the config tree on the right. Go down to `steps`.
    * Highlight the `+ add step` item and press <kbd>Enter</kbd>.
    * In the pop-up, enter the name `process_data` and save.
3.  **The Magic ✨:** When you save, two things happen automatically:
    * `process_data` is added to the `steps` list in your `config.yaml`.
    * A placeholder function `def process_data(...):` is scaffolded in `experiments/my-cli-experiment/steps.py`.

This allows you to design your pipeline declaratively. Now, open `steps.py` in your editor and add your logic to the placeholder function.

### Step 3: Running the Experiment 📊

Once your configuration and step logic are ready, it's time to run.

1.  **Launch the Run:** In the TUI's left panel, ensure your experiment is highlighted and press <kbd>Enter</kbd>.
2.  **Choose a Strategy:** The **Prepare Run** screen appears. This is a crucial step where you decide how to execute:
    * `rerun`: Executes everything from scratch. Use this for final runs or when you know the cache is invalid.
    * `resume`: Skips any steps that have already been completed successfully with the same inputs. This is perfect for iterating quickly after a failure or when you've only changed a downstream step.
3.  **Enable Minimal Targets:** For the first run, toggle on only `data_sources` and `steps` in the left panel, leaving the other sections off.
4.  **Start the Run:** Select the `rerun` option and confirm. The live runner displays logs and progress.
5.  **View the Summary:** When execution finishes, a summary screen appears showing tables of metrics and any hypothesis results collected during the run.
6.  **Increase Replicates:** Open your `config.yaml`, set `replicates` to `10`, and save.
7.  **Run Again:** Trigger another `rerun` from the TUI to execute all replicates and view the updated summary.

You've now gone from an idea to a fully executed, reproducible experiment, all managed through the CLI!
