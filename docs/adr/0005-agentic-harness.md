# ADR 0005: Introduce Agentic Harness Extensions

## Context & Problem

Validating spec-first, bounded synthesis workflows required higher-level components than the core Crystallize runner provided. We needed to layer claim/spec objects, sandboxed execution steps, and provenance capture without modifying existing core modules.

## Decision

Add a dedicated `agentic` package that supplies schema dataclasses, pipeline steps, verifiers, and provenance plugins. These pieces compose via public decorators and plugin hooks, preserving backwards compatibility with the framework core.

## Alternatives Considered

- **Modify core pipeline/experiment classes** – Discarded because the existing abstractions already support the required orchestration and changing them would increase regression risk.
- **Implement harness outside the repository** – Rejected to ensure shared typing, provenance, and testing live alongside the framework for easier maintenance.

## Consequences

- New first-class building blocks make it straightforward to orchestrate spec-first agentic flows using existing experiments.
- Additional tests and documentation were added to capture the new behaviour and ensure ongoing stability.
- Artifact directories now include prompt traces and evidence bundles when the new plugins are enabled, improving reproducibility at the cost of additional disk usage.
- The bounded execution capsule enforces AST allow-listing, runtime module diffing, and resource limits; Windows hosts fall back to wall-clock termination because `resource`-based limits are unavailable.
- Metamorphic checks execute inside the same sandbox to compare transformed inputs against baseline metrics, surfacing invariant regressions without halting the main replicate unless the sandbox itself fails.
