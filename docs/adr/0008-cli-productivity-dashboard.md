# ADR 0008: CLI Productivity Dashboard

## Context & Problem

The CLI selection screen relied on a nested tree, which made it hard to scan large sets of experiments, discover metadata, or quickly jump to a specific run target. Power users requested faster search and inline help without leaving the TUI.

## Decision

Replace the tree with a sortable data table that surfaces status, grouping, replicates, and last-run info, and add keyboard-first overlays for a fuzzy command palette (Ctrl+P) and a config cheat sheet (?).

## Alternatives Considered

- Keep the tree and add filters — simple but still low information density and limited sorting.
- Split experiments/graphs into tabs — clearer separation but added navigation steps and kept scanning slow.
- Search-only prompt without table — fast lookup but loses at-a-glance metadata and grouping context.

## Consequences

- Faster scanning and navigation with sortable columns plus a fuzzy palette for direct execution.
- Additional modal screens and CSS to maintain in the CLI; new bindings become part of the user-facing surface area.
- Status helper relies on lightweight filesystem checks; missing metadata yields neutral indicators until a run completes.
