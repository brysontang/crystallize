# ADR 0004: Deterministic Seed Mixing

## Context & Problem
Python's built-in `hash()` varies across interpreter sessions, leading to unstable seeds for experiment replicates and nondeterministic behavior across processes and threads.

## Decision
Use SHA-256 to mix the base seed and replicate number, taking the first 8 bytes as a 64-bit integer. This produces stable seeds across interpreter sessions and execution environments.

## Alternatives Considered
- Keep `hash()` – simple but non-deterministic across runs.
- Use `random.Random().seed()` combinations – still relies on non-stable hashing and is more complex.

## Consequences
- Stable, reproducible seeds across serial, threaded, and process executions.
- Minor computational overhead from SHA-256 hashing.
