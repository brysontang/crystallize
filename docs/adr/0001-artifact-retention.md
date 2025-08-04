# ADR 0001: Artifact retention and cache strategy

## Context & Problem

Repeated experiment runs produced unbounded artifact directories and large files, while the CLI lacked a clear distinction between reusing cached results and rerunning experiments.

## Decision

Introduce version pruning and size limits for artifacts, add experiment `strategy` defaults favouring resume behaviour, and load summary metrics directly from stored artifacts.

## Alternatives Considered

- Relying on manual cleanup — prone to disk growth.
- Always rerunning experiments — wastes compute when results already exist.

## Consequences

- Disk usage remains bounded to recent versions.
- Experiments run from the CLI reuse cached results unless explicitly unlocked.
- Summary screens show metrics for treatments from previous runs.
