# Changelog

All notable changes to this project are documented here. The project is currently in alpha; expect frequent updates until the API stabilises.

## [0.26.2](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.26.1...crystallize-ml@v0.26.2) (2025-12-26)


### Bug Fixes

* Correct test assertions and API usage ([56de06e](https://github.com/brysontang/crystallize/commit/56de06e756ae4c9bcc9a3fe6c876e7a2baca5e96))
* Remove unused imports and fix lint issues in tests ([f18a2e1](https://github.com/brysontang/crystallize/commit/f18a2e1dd076d90d83982d3a6b0138bf37fa85b6))


### Documentation

* Add comprehensive test coverage analysis ([80439f7](https://github.com/brysontang/crystallize/commit/80439f7c7f86c14992748b35ab98d591dec3383f))
* Add comprehensive test coverage analysis ([5f1b36a](https://github.com/brysontang/crystallize/commit/5f1b36a944d1774cb6dbf9b1cd24d3d33dec19fb))
* Polish architecture and glossary pages ([e11ac13](https://github.com/brysontang/crystallize/commit/e11ac136735699cf77b9c569ecc48290dcc0436d))
* Refresh test coverage analysis with completed improvements ([870799e](https://github.com/brysontang/crystallize/commit/870799e5901bb159ea4647075fe9b30f59118515))

## [0.26.1](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.26.0...crystallize-ml@v0.26.1) (2025-11-27)


### Bug Fixes

* Ensure deterministic seeding in parallel execution ([79483fd](https://github.com/brysontang/crystallize/commit/79483fd8dc42b4268c80f3728559d000bf9ebac8))
* Update docs ([fc4e726](https://github.com/brysontang/crystallize/commit/fc4e726d98c666128070458898bc6bb6869ff47a))


### Documentation

* Align documentation with v0.25.2 architecture and features ([3a7f8ae](https://github.com/brysontang/crystallize/commit/3a7f8ae6e3e1469271091111339fcd9fdffd236f))
* Fix build ([9325272](https://github.com/brysontang/crystallize/commit/93252723cc97062127e676455e04c53e23163aa0))

## [0.26.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.25.0...crystallize-ml@v0.26.0) (2025-11-27)


### Features

* Broaden editor detection for file-line launch ([e89b1dc](https://github.com/brysontang/crystallize/commit/e89b1dc26e494877a70fcb751dd3a193e9e0c4de))
* **cli:** Broaden editor detection for file-line launch ([d42fdd1](https://github.com/brysontang/crystallize/commit/d42fdd1e07cb0b10114ac85169c87bc362dca7ce))
* **cli:** Show artifact links in summary ([c33c355](https://github.com/brysontang/crystallize/commit/c33c3552016ab76c869ab7edc0b8e16a4f62b605))


### Bug Fixes

* Cache computation ([5329924](https://github.com/brysontang/crystallize/commit/53299247bb14520614d51478068f6d23ddd3b4e1))
* **cli:** Reset widget handler only when writer ([3656331](https://github.com/brysontang/crystallize/commit/3656331deeb00a1213fe90ef85d5e84ffbdb0dba))
* **cli:** Reset widget log handler each run ([f1d499d](https://github.com/brysontang/crystallize/commit/f1d499df6a86d2232df48b97e93c905df900bd57))
* Close WidgetWriter duplicate FDs ([d7de7ad](https://github.com/brysontang/crystallize/commit/d7de7adaceed53287708d06b81c0a1f6a63bc183))
* **crystallize-ml:** Close WidgetWriter duplicate FDs ([58e817f](https://github.com/brysontang/crystallize/commit/58e817f06cc5cfa49404c68e48af033c23f643fe))
* Enforce replicate consistency and add strict root finder option ([071f3c3](https://github.com/brysontang/crystallize/commit/071f3c314300b57b63877613f2862f11c992de1d))
* Improve process pickling diagnostics ([375fac4](https://github.com/brysontang/crystallize/commit/375fac4443070a9b328e25d640303761350af09c))
* Improve runtime stability and diagnostic output ([ac15de2](https://github.com/brysontang/crystallize/commit/ac15de2e4efafc13c86c79dde1171c1ce4292e34))
* Issue with subfolders and metadata ([a11602a](https://github.com/brysontang/crystallize/commit/a11602ab15ed4e96a45e3fad528b412eee995435))
* Log artifact baseline fallback and clean pipeline provenance ([b555b2d](https://github.com/brysontang/crystallize/commit/b555b2d37b5dcadc46a840132fdea7de7e0f86f2))
* Make more resistant ([c7aed26](https://github.com/brysontang/crystallize/commit/c7aed2647f0a77af46babded6f96cafbfa412f0c))
* Minor wording ([6ae4c3a](https://github.com/brysontang/crystallize/commit/6ae4c3abc3042c0c11e5bcd7694294593b4a8b31))
* Pypi deploy ([6c4b6ec](https://github.com/brysontang/crystallize/commit/6c4b6ec7993215917d7d91fd28208d46cf177dd6))
* Refine artifact fallback logging ([19d530d](https://github.com/brysontang/crystallize/commit/19d530d7e15164c7cf1ca15d0c120afb3fbae764))
* Returns artifacts ([ff786cc](https://github.com/brysontang/crystallize/commit/ff786cc6b2c56f178495a80d767ccf72b570a06d))


### Documentation

* Add artifact summary ADR ([e3e6e97](https://github.com/brysontang/crystallize/commit/e3e6e97d770a3f573a16068dfb748b9f86411b70))
* Record ADR for cooperative cancellation ([53323ec](https://github.com/brysontang/crystallize/commit/53323ec8bcdb800061e2d66b00ef3fa05a3111aa))
* Record pickling diagnostics decision ([394bc9d](https://github.com/brysontang/crystallize/commit/394bc9d80f9f28bbd60658b85f8a0776a47b2718))

## 0.25.1 (Unreleased)

### Added

- Textual-based CLI with experiment discovery, live logs, summary tab, artifact browser, and treatment toggles.
- YAML loader (`Experiment.from_yaml`, `ExperimentGraph.from_yaml`) with support for artifact references, output loaders/writers, and treatment state persistence.
- Fluent `Experiment.builder()` API and `Experiment.apply()` for single-shot inference.
- Optimisation helpers (`Experiment.optimize`, `Experiment.aoptimize`) built around an ask/tell `BaseOptimizer` interface.
- `generate_docs.py` script to regenerate API reference markdown via Lazydocs.
- Dependency injection is now strict: missing required parameters raise `TypeError`. Ensure `config.yaml` supplies all required arguments.

### Changed

- Package layout consolidated under `crystallize.{datasources,experiments,pipelines,plugins,utils}`.
- Default plugins now include artifact retention, auto seeding, and structured logging for every experiment.
- Artifact handling improved with manifest loading, version discovery, and writable `Artifact` objects that survive process-based execution.

### Fixed

- Experiment graphs honour cached runs when `strategy="resume"`, skipping nodes whose artifacts are complete.
- Treatment toggling state preserved in `.state.json`, preventing stale variants from rerunning unintentionally.
- CLI editor integration respects `$CRYSTALLIZE_EDITOR`, `$EDITOR`, and `$VISUAL`.
