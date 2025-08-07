# ADR 0004: Enforce Replicate Consistency in ExperimentInput

## Context & Problem
ExperimentInput previously inferred the number of replicates from only the first artifact input, which could mask mismatched replicate counts across artifacts.

## Decision
Gather replicates from all artifact inputs, raising a ValueError when conflicting counts are detected.

## Alternatives Considered
- **First artifact wins**: keep existing behavior and allow mismatches.
- **Silently pick max/min**: choose a replicate count without validation.

## Consequences
- **Positive**: Prevents subtle bugs caused by mixing artifacts with different replicate counts.
- **Negative**: Construction now errors if upstream artifacts are misconfigured.

