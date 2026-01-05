# Changelog

## [2.0.0-alpha.1](https://github.com/brysontang/crystallize/compare/crystallize-ml@v1.0.0-alpha.1...crystallize-ml@v2.0.0-alpha.1) (2026-01-05)


### ⚠ BREAKING CHANGES

* v1.0.0a2 - two-phase explore/crystallize API with audit ([#229](https://github.com/brysontang/crystallize/issues/229))

### Features

* V1.0.0a2 - two-phase explore/crystallize API with audit ([#229](https://github.com/brysontang/crystallize/issues/229)) ([d74a1ea](https://github.com/brysontang/crystallize/commit/d74a1eaf5a17d05d43c95976daa3bdba07189e0b))


### Bug Fixes

* Add prereleased trigger to publish workflow ([2e4efed](https://github.com/brysontang/crystallize/commit/2e4efed4f4c21dfcd2ced852e72e5001c39faa52))

## [1.0.0-alpha.2] - 2026-01-05

### New Features

- **`explore()` function**: Two-phase API replaces `run()`
  - Returns `Experiment` object that can be crystallized
  - `exp.crystallize(hypothesis, replicates)` for confirmatory runs
- **Protocol audit with `ctx.http`**: Instrumented HTTP wrapper tracks field provenance
  - `ctx.http.post()` / `ctx.http.get()` for audited API calls
  - Automatic provenance detection: `config.*`, `hardcoded`, `implicit_default`
- **Hidden variables detection**: `exp.hidden_variables()` reports uncontrolled parameters
  - Risk levels: HIGH (sensitive fields), MED (hardcoded), LOW (non-sensitive)
- **Fresh replicate management**: Lineage tracking ensures no data reuse
  - Ledger tracks replicate indices per lineage/config
  - Pre-registration artifacts written before sampling
- **Integrity status**: `ConfirmRun.integrity` shows VALID, CONFOUNDED, REUSED_DATA, etc.
  - Override flags: `allow_reuse`, `allow_confounds`, `allow_no_audit`, `allow_fn_change`
- **Permutation test**: Non-parametric statistical test (no distributional assumptions)
- **Bootstrap CI**: 95% confidence intervals for effect sizes
- **Function fingerprinting**: Detects if experiment function changed between runs
- **Git integration**: Auto-captures commit SHA and dirty status

### New Modules

- `crystallize/core.py` - explore(), Experiment, crystallize(), ConfirmRun
- `crystallize/context.py` - Enhanced Context with ctx.http
- `crystallize/http.py` - InstrumentedHTTP wrapper
- `crystallize/protocol.py` - ProtocolEvent, HiddenVariable, ProtocolDiff
- `crystallize/stats.py` - permutation_test, bootstrap_ci
- `crystallize/integrity.py` - IntegrityStatus, compute_integrity
- `crystallize/store.py` - .crystallize/ filesystem, atomic writes, ledger
- `crystallize/ids.py` - run_id, lineage_id, config_fingerprint
- `crystallize/fingerprint.py` - Function fingerprinting

### Deprecated

- `run()` function: Still works but prints deprecation warning. Use `explore()` instead.

---

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
