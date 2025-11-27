# ADR 0007: Result Aggregation and CLI Extras Guard

## Context & Problem

Experiment was accumulating result aggregation and provenance building logic, making it harder to evolve independently. The CLI also attempted to load `crystallize_extras` steps without verifying the optional package, leading to confusing runtime import errors. Config validation missed clear errors for malformed experiment YAML.

## Decision

Extract result aggregation into a dedicated `ResultAggregator` helper and delegate from `Experiment`. Add a CLI check that detects `crystallize_extras` steps during discovery and raises a friendly dependency error. Tighten `Experiment.from_yaml` validation to surface missing datasource and verifier references explicitly.

## Alternatives Considered

- Keep aggregation methods on `Experiment`; rejected to avoid further god-object bloat.
- Defer extras detection to runtime imports; rejected because it yields opaque ImportErrors in the TUI.
- Leave YAML validation as-is; rejected because downstream stack traces were unclear for missing sections.

## Consequences

- Clearer separation of aggregation responsibilities and easier reuse in future executors.
- CLI surfaces actionable guidance when optional extras are unavailable.
- YAML configs fail fast with targeted errors, with new tests capturing the behaviors.
