# ADR 0002: Treatment Panel Toggle and Summary Flow

## Context & Problem
RunScreen lacked a way to activate, deactivate, or inspect treatments, and summaries omitted inactive treatments.

## Decision
Persist inactive treatment names, expose them in the sidebar with color-coded toggles, and load metrics from the latest and prior artifact versions so summaries include treatments even after they are disabled. Helpers manage YAML edits for adding new treatments.

## Alternatives Considered
- Only track treatment state in memory.
- Embed YAML editing logic directly in RunScreen.

## Consequences
- Users can manage treatments without leaving the run UI.
- Additional state file (`*.state.json`) per config and extra code paths to maintain.
