# ADR 0006: Deterministic Seeding Across Executors

## Context & Problem

The SeedPlugin relied on Python's `hash()` to derive per-replicate seeds, which is salted per process and produced divergent seeds across executors. Thread-based execution also shared global RNG state, making reproducibility unreliable.

## Decision

Compute replicate seeds deterministically using a master seed plus a fixed arithmetic offset, and warn users when combining SeedPlugin with thread executors since the RNG state is shared. Default seeding now covers both `random` and `numpy` when no custom seed function is supplied.

## Alternatives Considered

- Keep using `hash()` for per-replicate seeds (non-deterministic across processes).
- Require callers to supply fully custom seed functions for reproducibility (less ergonomic, easy to misconfigure).
- Serialize thread execution with locks to isolate RNG state (would undermine parallelism benefits).

## Consequences

- Seeds are stable across serial and process-based execution, fixing prior nondeterminism.
- Thread executors remain non-deterministic but now emit an explicit warning.
- Existing runs that relied on the old hash-derived seeds will observe different seed values going forward.
