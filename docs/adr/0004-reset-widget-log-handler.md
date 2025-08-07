# ADR 0004: Reset Widget Log Handler Each Run

## Context & Problem
Reloading the TUI left old `WidgetLogHandler` instances attached to the `crystallize` logger. Subsequent runs could miss log messages or display them multiple times.

## Decision
`TextualLoggingPlugin.before_run` now removes existing handlers and attaches a fresh `WidgetLogHandler` for each run when a writer is available, guaranteeing exactly one active handler.

## Alternatives Considered
- **Keep existing handler:** left stale widget bindings and duplicated logs.
- **Track handlers via global state:** added unnecessary complexity and state management.

## Consequences
- Logging remains consistent across sequential runs.
- Minor overhead of re-creating the handler every run.
