---
title: Reproducibility
description: The design choices in Crystallize that ensure experiments can be reproduced exactly.
---

Crystallize is engineered so that every experiment can be repeated with identical results. Four core features work together to guarantee this reproducibility.

## Immutable Contexts

`FrozenContext` stores all parameters and metrics during execution. It disallows mutation of existing keys, raising a `ContextMutationError` if a step tries to overwrite a value. By preventing accidental state changes, each replicate runs in a clean, predictable environment.

## Deterministic Seeding

Randomness is controlled by the `SeedPlugin`. It sets a unique seed for every replicate and records the value in the context. Any function that relies on randomness—data sampling, shuffling, or model initialization—receives the same seed for a given replicate, ensuring identical behavior when rerun.

Each replicate seed is derived from the master seed with the formula `(master_seed + replicate_id * 31337) % 2**32`. Using a fixed multiplier keeps the mapping stable across Linux and macOS and preserves identical seeds for serial and process-based execution modes.

Thread executors share global RNG state, so they emit a warning and should be avoided when strict reproducibility is required.

## Content-Based Caching

Each `PipelineStep` is hashed along with its inputs. When a step is cacheable, Crystallize checks whether the combination of step parameters and input data has been seen before. If so, it loads the cached output instead of recomputing it. This guarantees that equal inputs always lead to equal outputs while also saving computation time.

## Declarative Experiments

The `Experiment` class defines data sources, pipelines, treatments, hypotheses, and plugins purely in code. Because the entire configuration lives in a Python module (or YAML file), it can be version controlled and shared. Re-running an experiment with the same code and data reproduces the exact sequence of steps and results.
