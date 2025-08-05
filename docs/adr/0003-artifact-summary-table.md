# ADR 0003: Link artifacts in experiment summary

## Context & Problem
The CLI summary only displayed metrics and hypothesis results, making it hard to locate artifacts generated during runs.

## Decision
Record artifact file paths during experiment execution and render them in a summary table with clickable links.

## Alternatives Considered
- Rely on manual file browsing to inspect artifacts.
- Show artifact names without linking to their locations.

## Consequences
- Users can open produced artifacts directly from the summary.
- Result objects now store paths to artifacts, increasing memory usage slightly.
