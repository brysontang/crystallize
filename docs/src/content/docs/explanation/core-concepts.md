---
title: Core Concepts
description: High-level overview of the main abstractions in Crystallize.
---

Crystallize organizes every experiment around a set of focused, decoupled pieces. Understanding these components helps you build clear and reproducible workflows.

## The Experiment

The `Experiment` class is the conductor of a Crystallize run. It combines your data source and pipeline into an execution machine.  When calling ``experiment.run()``, you provide the treatments and hypotheses to evaluate.  The experiment executes the baseline and each treatment across the requested replicates, collects metrics, and verifies them using the supplied hypotheses.

See the [Building Your First Experiment tutorial](../tutorials/basic-experiment.md) for a walkthrough of the experiment lifecycle.

## DataSource

A `DataSource` is responsible for fetching or generating the raw input for your pipeline. By isolating data loading in its own component, Crystallize makes it easy to swap sources or parameterize them with treatments. Data sources are deterministic and receive the immutable context so they can react to experimental parameters.

You can explore a simple implementation in the [getting started tutorial](../tutorials/intro.md).

## Pipeline & PipelineStep

A `Pipeline` is an ordered list of `PipelineStep` objects. Each step performs a deterministic transformation on data, returning the new value for the next step. Steps receive a frozen execution context and can record metrics. Because steps are deterministic, Crystallize automatically caches their outputs by content hash to ensure reproducible reruns.

Learn how to design your own steps in [Creating Custom Pipeline Steps](../how-to/custom-steps.md).

## Treatment

Treatments define experimental variations. They inject new values into the context for downstream steps to use, allowing you to compare the baseline against alternate configurations. Treatments never mutate existing context keys, ensuring that every run is isolated and deterministic.

See [Adding Treatments](../tutorials/adding-treatments.md) for practical examples.

## Hypothesis & Verifier

A `Hypothesis` represents a quantifiable claim about your experiment's outcome. Each hypothesis references one or more metrics and uses a `Verifier` to compare baseline and treatment samples. A verifier returns statistics such as p-values or confidence intervals, and the hypothesis optionally ranks treatments according to those results.

For details on writing hypotheses and integrating statistical tests, check the [Verifying Hypotheses tutorial](../tutorials/hypotheses.md) and [Integrating Statistical Tests](../how-to/integrate-stats.md).

## Optimizer

An optimizer drives an iterative search over treatments. It implements an `ask`/`tell` interface that the `Experiment.optimize()` method calls each trial. Optimizers remain unopinionated in the core library so you can plug in grid search, Bayesian algorithms, or any strategy you like.

## Plugin Architecture

Plugins extend Crystallize without subclassing the core classes. They hook into the experiment lifecycle—initialization, before and after each replicate, after each step, and at completion. Built-in plugins handle tasks such as seeding random number generators, running steps in parallel, and saving artifacts, but you can create your own to add logging or custom execution logic.

Read [Creating Custom Plugins](../how-to/creating-plugins.md) and [Customizing Experiments](../how-to/customizing-experiments.md) to see the plugin system in action.
