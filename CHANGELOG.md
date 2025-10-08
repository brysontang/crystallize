# Changelog

All notable changes to this project are documented here. The project is currently in alpha; expect frequent updates until the API stabilises.

## 0.25.1 (Unreleased)

### Added

- Textual-based CLI with experiment discovery, live logs, summary tab, artifact browser, and treatment toggles.
- YAML loader (`Experiment.from_yaml`, `ExperimentGraph.from_yaml`) with support for artifact references, output loaders/writers, and treatment state persistence.
- Fluent `Experiment.builder()` API and `Experiment.apply()` for single-shot inference.
- Optimisation helpers (`Experiment.optimize`, `Experiment.aoptimize`) built around an ask/tell `BaseOptimizer` interface.
- `generate_docs.py` script to regenerate API reference markdown via Lazydocs.

### Changed

- Package layout consolidated under `crystallize.{datasources,experiments,pipelines,plugins,utils}`.
- Default plugins now include artifact retention, auto seeding, and structured logging for every experiment.
- Artifact handling improved with manifest loading, version discovery, and writable `Artifact` objects that survive process-based execution.

### Fixed

- Experiment graphs honour cached runs when `strategy="resume"`, skipping nodes whose artifacts are complete.
- Treatment toggling state preserved in `.state.json`, preventing stale variants from rerunning unintentionally.
- CLI editor integration respects `$CRYSTALLIZE_EDITOR`, `$EDITOR`, and `$VISUAL`.
