# ADR 0005: Strong Experiment IDs

## Context & Problem
Experiment identifiers were derived solely from the pipeline signature, so runs with identical pipelines but different datasource parameters or treatments could collide.

## Decision
Introduce optional strong identifiers that incorporate datasource parameters, treatment details, and replicates when the environment variable `CRYSTALLIZE_STRONG_IDS=1` is set.

## Alternatives Considered
- Always include datasource and treatment details in the identifier – would break existing experiment directories and caches.
- Use random or timestamp-based IDs – sacrifices reproducibility and traceability.

## Consequences
- Default behaviour remains unchanged, ensuring backward compatibility.
- When enabled, experiments with different datasources, treatments, or replicate counts produce distinct IDs, reducing collisions.
- Slightly more computation is required to hash the richer payload.
