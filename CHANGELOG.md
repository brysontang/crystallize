# Changelog

## [1.0.0-alpha.1] - 2026-01-05

### Breaking Changes

Complete rewrite of Crystallize. The entire framework has been replaced with a single, simple API.

### What's New

- **`run()` function**: The entire API is now one function
- **Exploratory mode**: No hypothesis required - just play around
- **Confirmatory mode**: Add `hypothesis=` to prove something
- **Progress bar**: Built-in rich progress display
- **Statistical output**: p-values, effect sizes, sample counts
- **`on_event` callback**: For live viewer integration
- **`ctx.record()`**: Simple metrics recording with optional tags

### What's Removed

- Datasources, pipelines, treatments, plugins
- CLI/TUI interface
- YAML configuration
- ExperimentGraph/DAG orchestration
- All extras (ollama, ray, vllm, openai)

### Migration

The old framework is preserved at:
- Tag: `v0.27.0-final`
- Branch: `legacy/v0.x`

For v0.x users: pin `crystallize-ml<1.0` or migrate to the new `run()` API.

---

## Previous Releases (v0.x)

See the [legacy/v0.x branch](https://github.com/brysontang/crystallize/tree/legacy/v0.x) for the full v0.x changelog.
