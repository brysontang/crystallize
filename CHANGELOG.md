## [0.6.1](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.6.0...crystallize-ml@v0.6.1) (2025-07-15)

### Documentation

- Add retrospective changelogs for main and extras packages ([ad715ae](https://github.com/brysontang/crystallize/commit/ad715ae23e0e00c17bf86f77f1ce808a855fc7e7))
- Update reference docs and generation workflow ([10bcec4](https://github.com/brysontang/crystallize/commit/10bcec461da38eb09cd2cfbcdf0d36be1f03ad3d))

## [0.9.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.8.1...crystallize-ml@v0.9.0) (2025-07-18)


### Features

* Add ResourceHandle and improve step init ([63ce75e](https://github.com/brysontang/crystallize/commit/63ce75ed4b84db2e589824dadfe1b1b046cec9e0))
* **crystallize-ml:** Add ResourceHandle utility ([07e5102](https://github.com/brysontang/crystallize/commit/07e5102ea050ef42f56abee056518579c48bf4ff))


### Documentation

* Auto-update generated API docs ([8b71015](https://github.com/brysontang/crystallize/commit/8b71015d434a2ebed636c03cac34aa92786d6b84))

## [0.8.1](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.8.0...crystallize-ml@v0.8.1) (2025-07-18)


### Bug Fixes

* **crystallize-ml:** Ollama base_url -&gt; host ([10be1d1](https://github.com/brysontang/crystallize/commit/10be1d1e3a113a5107e26a5583e89af2ad4fa26b))
* **crystallize-ml:** Ollama base_url -&gt; host ([adc3319](https://github.com/brysontang/crystallize/commit/adc33194c42d623498401e947e6b79b37379663f))

## [0.8.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.7.0...crystallize-ml@v0.8.0) (2025-07-18)


### Features

* **crystallize-ml:** Add plugin lifecycle to apply ([fb0e288](https://github.com/brysontang/crystallize/commit/fb0e28861cc4dc0b97da34151e8a3821931cd93f))
* **crystallize-ml:** Apply uses full lifecycle ([9c58a07](https://github.com/brysontang/crystallize/commit/9c58a074b1ccc84dc75f1e2c30d74f30bc2e1657))

## [0.7.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.6.2...crystallize-ml@v0.7.0) (2025-07-18)


### Features

* **crystallize-extras:** Add Ollama client step ([9c5e91e](https://github.com/brysontang/crystallize/commit/9c5e91e6eb00b77b9e2a1b0a4a76bbe2e77be98f))
* **crystallize-ml:** Chain experiments via artifact datasource ([7c718a6](https://github.com/brysontang/crystallize/commit/7c718a6bea6b67fdeae7519302906ca04913ed6b))
* **crystallize-ml:** Polish artifact datasource ([c784139](https://github.com/brysontang/crystallize/commit/c7841392dd84dd378d189f70a4f63ee0fc454695))
* **crystallize-ml:** Return artifact paths ([0077c1e](https://github.com/brysontang/crystallize/commit/0077c1ee159c97dcdf2f75a2ec0703d33b0500ed))

## [0.6.2](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.6.1...crystallize-ml@v0.6.2) (2025-07-15)


### Bug Fixes

* Crystallize.core now exports classes ([d7456be](https://github.com/brysontang/crystallize/commit/d7456beb4955c06474485c5685857b98f4bd7618))
* Double import ([41a5a2d](https://github.com/brysontang/crystallize/commit/41a5a2d45cbdbed177099cfae3d6a38e5a9abb74))


### Documentation

* Add full workflow tutorial ([fa372b6](https://github.com/brysontang/crystallize/commit/fa372b6b715f2e27e8333fa7617683ecf32e1538))
* Added code2prompt command ([81fb94f](https://github.com/brysontang/crystallize/commit/81fb94f43e573a7706349f44a79bdf531e996774))

## [0.6.0] - 2025-07-14

- Add context-aware parameter injection

## [0.5.0] - 2025-07-14

- Enhance docstrings across core modules
- Finalize optimizer abstraction and refactor Experiment

## [0.4.0] - 2025-07-14

- Refactor docs for new Experiment API
- Introduce plugin architecture for experiment
- Remove deprecated experiment builder
- Implement Artifact Management System
- Add core concepts doc
- Add reproducibility docs
- Add parallelism explanation doc
- Add extension architecture docs
- Add documentation comparing Crystallize to other tools
- Add FAQ documentation

## [0.3.1] - 2025-07-13

- Fix parallel provenance
- Investigate provenance issue in minimal example

## [0.3.0] - 2025-07-13

- Add extensive unit tests for core components
- Introduce dataclass metrics
- Add auto seeding to experiments
- Add guide on customizing experiments
- Add how-to guide for custom pipeline steps
- Add provenance tree summary
- Improve print_tree color hierarchy
- Add run verbosity features

## [0.2.0] - 2025-07-12

- Add decorator-based pipeline API
- Add multi-hypothesis support
- Add experiment apply mode and optional configs
- Add builder pattern and validation to Experiment
- Update examples to use decorators
- Improve context and treatment usability
- Add tests for edge cases across core components
- Introduce ExperimentBuilder
- Refactor Hypothesis verifier API
- Add metrics context and ranking
- Add missing type hints
- Add optional parallel experiment execution

## [0.1.0] - 2025-07-9

- Add unit tests for core components
- Implement explicit custom exceptions
- Implement pipeline caching with provenance
- Add CSV pipeline example
- Add YAML CLI interface
