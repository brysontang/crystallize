# ADR 0004: Improve pickling diagnostics in ParallelExecution

## Context & Problem
Parallel execution with a process pool fails when experiments contain non-picklable objects. The previous error message did not identify the experiment or offer guidance, making debugging difficult.

## Decision
Catch pickling errors in `ParallelExecution` and raise a detailed `RuntimeError` that includes the experiment name, pipeline step names, and suggestions to avoid non-picklable closures or to wrap heavy resources with `resource_factory`.

## Alternatives Considered
- Keeping the generic error message.
- Logging diagnostic information instead of raising a richer error.

## Consequences
- Provides actionable guidance when pickling fails.
- Slightly increases error message verbosity.
