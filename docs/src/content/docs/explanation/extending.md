---
title: Extending Crystallize
description: Philosophy and primary patterns for extending the framework.
---

Crystallize is intentionally minimal. Its architecture emphasizes clear data transformations and reproducible workflows. Rather than subclassing core classes, you extend functionality through a small set of well-defined extension points. This guide outlines those points and the guiding principles behind them.

## Plugins: The Primary Extension Mechanism

Plugins allow you to inject behavior around the execution of an experiment. Each plugin subclasses `BasePlugin` and implements any of the available **lifecycle hooks**:

- `init_hook(experiment)`: configure defaults when the experiment instance is created.
- `before_run(experiment)`: run logic at the start of `run()` before replicates execute.
- `before_replicate(experiment, ctx)`: invoked prior to each replicate's pipeline.
- `after_step(experiment, step, data, ctx)`: observe the output of every `PipelineStep`. Do not mutate `data` or `ctx` here.
- `after_run(experiment, result)`: called after the result object is assembled.
- `run_experiment_loop(experiment, replicate_fn)`: optional hook to override how replicates are executed (e.g., parallelism).

Use plugins for **cross-cutting operational concerns** such as logging, notifications, artifact storage, or custom execution strategies. Keep data transformations inside pipeline steps; plugins should be side-effect oriented observers or coordinators.

### Design Principle

1. **Transform data with `PipelineStep` implementations.** Steps are pure functions that take `data` and `ctx` and return new data.
2. **Handle operational logic with plugins.** Anything related to orchestration, metrics aggregation, saving outputs, or monitoring belongs in a plugin.

This separation keeps pipelines focused and testable while enabling rich customization of experiment behavior.

## Other Extension Points

While plugins are the main mechanism, you can also extend Crystallize by:

- **Creating custom `DataSource` classes** to fetch or generate your input data.
- **Writing new `@verifier` functions** for hypotheses, providing statistical tests or custom ranking logic.

Together these extension points allow advanced users to tailor Crystallize to unique workflows without modifying the core library.
