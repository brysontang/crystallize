# ADR 0004: Cache duplicate FD in WidgetWriter

## Context & Problem

`WidgetWriter.fileno()` duplicated the real stdout file descriptor on each call, leaking descriptors during long-running sessions.

## Decision

Cache a single duplicated file descriptor within `WidgetWriter` and close it explicitly when runs finish.

## Alternatives Considered

- Duplicate on every `fileno()` call – simple but leaks descriptors.
- Return `sys.__stdout__.fileno()` directly – risks interference with the real stdout in multiprocessing contexts.

## Consequences

- Prevents file descriptor leaks across runs.
- Requires plugins to close the `WidgetWriter` after use to release the descriptor.
