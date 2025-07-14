---
title: How Crystallize Compares to Other Tools
description: Positioning of Crystallize relative to experiment trackers, notebooks, data versioning, and workflow orchestrators.
---

Crystallize focuses on turning hypotheses into clear, reproducible experiments. It complements rather than replaces many popular data science and MLOps tools. The sections below outline how Crystallize fits alongside other solutions in the ecosystem.

## vs. Experiment Trackers (MLflow, Weights & Biases)

Experiment trackers record metrics, parameters, and artifacts from runs. They excel at visualizing results and keeping a history of experiments. Crystallize is an execution framework: it structures the entire hypothesis-testing loop—data source, pipeline, treatments, and statistical verification. To store metrics in an external tracker, Crystallize can use a plugin that forwards results to MLflow, Weights & Biases, or another tracking system.

## vs. Notebooks (Jupyter)

Jupyter notebooks are excellent for interactive exploration and rapid prototyping. Crystallize provides the structure and reproducibility needed to transform that exploratory code into formal experiments. By defining steps, treatments, and hypotheses as reusable components, Crystallize scales experiments beyond the confines of a single notebook while ensuring consistent, repeatable runs.

## vs. Data Versioning/Pipelining (DVC, Pachyderm)

Tools such as DVC and Pachyderm manage datasets and data-centric pipelines. They track versions of data and orchestrate transformations across large files or distributed storage. Crystallize operates at a different layer: it focuses on the experimental workflow—the sequence of treatments, metrics, and statistical tests that validate a hypothesis. Crystallize can be used alongside data versioning tools if your experiments require robust data provenance.

## vs. Workflow Orchestrators (Airflow, Prefect)

Workflow orchestrators coordinate diverse tasks across infrastructure. They are general-purpose platforms for scheduled or event-driven pipelines. Crystallize is specialized for scientific experimentation. Concepts like **Treatment** and **Hypothesis** are built into its core, so you can express experiments directly without managing low-level orchestration details. For larger systems, Crystallize can be invoked from a broader orchestrator when experiments need to fit within an existing workflow.
