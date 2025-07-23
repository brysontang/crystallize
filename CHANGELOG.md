## [0.6.1](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.6.0...crystallize-ml@v0.6.1) (2025-07-15)

### Documentation

- Add retrospective changelogs for main and extras packages ([ad715ae](https://github.com/brysontang/crystallize/commit/ad715ae23e0e00c17bf86f77f1ce808a855fc7e7))
- Update reference docs and generation workflow ([10bcec4](https://github.com/brysontang/crystallize/commit/10bcec461da38eb09cd2cfbcdf0d36be1f03ad3d))

## [0.17.1](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.17.0...crystallize-ml@v0.17.1) (2025-07-23)


### Bug Fixes

* **crystallize-ml:** Handle artifact datasource ([54ae23d](https://github.com/brysontang/crystallize/commit/54ae23d797f9864b2eee6cd0ab550f3107b314ae))

## [0.17.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.16.0...crystallize-ml@v0.17.0) (2025-07-22)


### Features

* Add apply mode and optional components ([c886505](https://github.com/brysontang/crystallize/commit/c886505d50b4f355611d5286f1b6278a479590d9))
* Add caching and provenance ([5ed6e67](https://github.com/brysontang/crystallize/commit/5ed6e671cb7d03d0e1afac08822f32addb6bdb4e))
* Add context parameter injection ([447cd61](https://github.com/brysontang/crystallize/commit/447cd614d3b91dfa48ad5766e9ef9ae41154f199))
* Add deterministic auto seeding ([c510312](https://github.com/brysontang/crystallize/commit/c510312bb0b5d4bc53ad27c0e9cfd26d719ec3df))
* Add ResourceHandle and improve step init ([63ce75e](https://github.com/brysontang/crystallize/commit/63ce75ed4b84db2e589824dadfe1b1b046cec9e0))
* **crystallize-extras:** Add Ollama client step ([9c5e91e](https://github.com/brysontang/crystallize/commit/9c5e91e6eb00b77b9e2a1b0a4a76bbe2e77be98f))
* **crystallize-extras:** Openai client ([57b7058](https://github.com/brysontang/crystallize/commit/57b70585d6c1c5646fae4e22ce36aef604e41473))
* **crystallize-extras:** Openai client ([1f6c10e](https://github.com/brysontang/crystallize/commit/1f6c10eedc86a6e6e423895cf0b7a0d3af407dbe))
* **crystallize-ml:** Add experiment name for artifact paths ([171c94f](https://github.com/brysontang/crystallize/commit/171c94f8028818021bf1ae2ce057da3318475296))
* **crystallize-ml:** Add logger to context ([86b3606](https://github.com/brysontang/crystallize/commit/86b3606d9766633f34dbfcbafb0f4e4c0fe67cf1))
* **crystallize-ml:** Add Output class and resume strategy ([60744bb](https://github.com/brysontang/crystallize/commit/60744bb610ed61547bdfef3aab651943f5bbe6ca))
* **crystallize-ml:** Add plugin lifecycle to apply ([fb0e288](https://github.com/brysontang/crystallize/commit/fb0e28861cc4dc0b97da34151e8a3821931cd93f))
* **crystallize-ml:** Add ResourceHandle utility ([07e5102](https://github.com/brysontang/crystallize/commit/07e5102ea050ef42f56abee056518579c48bf4ff))
* **crystallize-ml:** Apply uses full lifecycle ([9c58a07](https://github.com/brysontang/crystallize/commit/9c58a074b1ccc84dc75f1e2c30d74f30bc2e1657))
* **crystallize-ml:** Auto build experiment graph ([cc7c1b7](https://github.com/brysontang/crystallize/commit/cc7c1b78e2e16f4d962deac1ed302ebc13096168))
* **crystallize-ml:** Chain experiments via artifact datasource ([7c718a6](https://github.com/brysontang/crystallize/commit/7c718a6bea6b67fdeae7519302906ca04913ed6b))
* **crystallize-ml:** Flatten public api ([659ca6a](https://github.com/brysontang/crystallize/commit/659ca6a467bc890eb4e37572c0b6d3fe79b983bd))
* **crystallize-ml:** Improve artifact datasource ([844bb00](https://github.com/brysontang/crystallize/commit/844bb0079bf62eb431ec9101c5d2814aafada2fa))
* **crystallize-ml:** Improve ExperimentGraph and tests ([d532e2d](https://github.com/brysontang/crystallize/commit/d532e2da72da8f2ec820c498f57a66be87d2755c))
* **crystallize-ml:** Introduce Artifact and ExperimentInput ([05ee063](https://github.com/brysontang/crystallize/commit/05ee063d9423c457d6fab4459e833e4109d55ea4))
* **crystallize-ml:** Make experiment methods stateless ([aad502d](https://github.com/brysontang/crystallize/commit/aad502d6922d4b6bcd57bb701c1aa7b59fb81c73))
* **crystallize-ml:** Make experiment state stateless ([0601416](https://github.com/brysontang/crystallize/commit/060141610423623fb6daf1721a2bb2c661d49ff7))
* **crystallize-ml:** Make experiment stateless ([f7c24a3](https://github.com/brysontang/crystallize/commit/f7c24a3e6a5ba612365690d9b20a39c830640434))
* **crystallize-ml:** Polish artifact datasource ([c784139](https://github.com/brysontang/crystallize/commit/c7841392dd84dd378d189f70a4f63ee0fc454695))
* **crystallize-ml:** Refine resume logic ([ee6a787](https://github.com/brysontang/crystallize/commit/ee6a787e5326c6a2387be3f5ca713910272d8db2))
* **crystallize-ml:** Return artifact paths ([0077c1e](https://github.com/brysontang/crystallize/commit/0077c1ee159c97dcdf2f75a2ec0703d33b0500ed))
* **crystallize-ml:** Simplify resources with factories ([df5457b](https://github.com/brysontang/crystallize/commit/df5457bbcaaad1b3ebd19aaf6bfe2273c9a3c848))
* **crystallize-ml:** Stateless experiment runs ([caf9f1f](https://github.com/brysontang/crystallize/commit/caf9f1f7d15595da661037d75cd9c97672b14301))
* Support multiple hypotheses ([27ed2e3](https://github.com/brysontang/crystallize/commit/27ed2e3971b777ccc7e5f1cb176f784b6bc6d717))


### Bug Fixes

* .apply adds the step setup to ctx ([171c94f](https://github.com/brysontang/crystallize/commit/171c94f8028818021bf1ae2ce057da3318475296))
* .apply adds the step setup to ctx ([f96ff2c](https://github.com/brysontang/crystallize/commit/f96ff2c2d55b57ed552aa096e56d910b723bf3f3))
* **crystallize-ml:** Allow decorated objects to be pickled ([654fc3b](https://github.com/brysontang/crystallize/commit/654fc3b8687f83ffa5b8e6b68bdfedea29bd4810))
* **crystallize-ml:** Ollama base_url -&gt; host ([10be1d1](https://github.com/brysontang/crystallize/commit/10be1d1e3a113a5107e26a5583e89af2ad4fa26b))
* **crystallize-ml:** Ollama base_url -&gt; host ([adc3319](https://github.com/brysontang/crystallize/commit/adc33194c42d623498401e947e6b79b37379663f))
* **crystallize-ml:** Pickle issue ([6830ac3](https://github.com/brysontang/crystallize/commit/6830ac3bbefeb6eaf5dc6d60c611d267d89f5374))
* **crystallize-ml:** Refine factory caching and injection ([0b3af92](https://github.com/brysontang/crystallize/commit/0b3af92ca18e5f5de3ff3b7e14a26eb01ff32a91))
* **crystallize-ml:** Refine logging and CLI output ([74bb33d](https://github.com/brysontang/crystallize/commit/74bb33d79f9a8f9990934001f4a5c1cc83accfd6))
* **crystallize-ml:** Resolve tests for new Artifact API ([02ec241](https://github.com/brysontang/crystallize/commit/02ec241efeb81cfe60a4c52f75b5622c5b765ca9))
* **crystallize-ml:** Restore dataclasses for results ([ac0fbfb](https://github.com/brysontang/crystallize/commit/ac0fbfb5bc02cbbb7809d52ecea0815cef389263))
* **crystallize-ml:** Set replicates default in apply ([fc3e75c](https://github.com/brysontang/crystallize/commit/fc3e75cd26a2eee2109daf440981fe9c1db27ddd))
* **crystallize-ml:** Update examples and tests ([32e35f4](https://github.com/brysontang/crystallize/commit/32e35f473ea1a7237e89e4fad69a38b94041bc93))
* Crystallize.core now exports classes ([d7456be](https://github.com/brysontang/crystallize/commit/d7456beb4955c06474485c5685857b98f4bd7618))
* Double import ([41a5a2d](https://github.com/brysontang/crystallize/commit/41a5a2d45cbdbed177099cfae3d6a38e5a9abb74))


### Documentation

* Add core concepts overview ([042bc8d](https://github.com/brysontang/crystallize/commit/042bc8dbb3ac78c116b8d05fe8c937abbbb5617c))
* Add FAQ document ([e15f7c5](https://github.com/brysontang/crystallize/commit/e15f7c5a98e01965b49895e9c2b7f6d37f095cd4))
* Add framework extension guide ([73cb6bb](https://github.com/brysontang/crystallize/commit/73cb6bbd383e5aae0d26f6c2b2fb725afeafc769))
* Add full workflow tutorial ([fa372b6](https://github.com/brysontang/crystallize/commit/fa372b6b715f2e27e8333fa7617683ecf32e1538))
* Add optimization tutorial and reference ([262ce0e](https://github.com/brysontang/crystallize/commit/262ce0ed67e6614e51b96c20c211c3df41252401))
* Add parallelism explanation ([e3590f0](https://github.com/brysontang/crystallize/commit/e3590f0f6dfdcdf6f434519753e9460681d021c2))
* Add reproducibility section ([b61d62e](https://github.com/brysontang/crystallize/commit/b61d62e472a0a056ca436cb5ded0293284b74afb))
* Add retrospective changelogs for main and extras packages ([ad715ae](https://github.com/brysontang/crystallize/commit/ad715ae23e0e00c17bf86f77f1ce808a855fc7e7))
* Added code2prompt command ([81fb94f](https://github.com/brysontang/crystallize/commit/81fb94f43e573a7706349f44a79bdf531e996774))
* Auto-update generated API docs ([34375ed](https://github.com/brysontang/crystallize/commit/34375ed5296369127b220904cc4f09fdc6fa130c))
* Auto-update generated API docs ([6302344](https://github.com/brysontang/crystallize/commit/63023449b48c5ae050ff782af1ad7453b6edb5de))
* Auto-update generated API docs ([3e7bcb1](https://github.com/brysontang/crystallize/commit/3e7bcb16930b45493ea89f3186bc862eb251b095))
* Auto-update generated API docs ([f9b6cb9](https://github.com/brysontang/crystallize/commit/f9b6cb934e441a9ec2af24535cc31825162c36b2))
* Auto-update generated API docs ([8b71015](https://github.com/brysontang/crystallize/commit/8b71015d434a2ebed636c03cac34aa92786d6b84))
* **crystallize-ml:** Document Result.print_tree ([28bbf3a](https://github.com/brysontang/crystallize/commit/28bbf3aaa75dd0e0056fefe2ad94bf87a1a5225f))
* Document context injection ([6699023](https://github.com/brysontang/crystallize/commit/6699023e79d5d62af9ff8b7a47da19a11208b935))
* Fix glossary link for custom steps ([d430522](https://github.com/brysontang/crystallize/commit/d430522a2869f026044496cc95d8bd86007ff582))
* Update reference docs and generation workflow ([10bcec4](https://github.com/brysontang/crystallize/commit/10bcec461da38eb09cd2cfbcdf0d36be1f03ad3d))

## [0.16.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.15.0...crystallize-ml@v0.16.0) (2025-07-22)


### Features

* **crystallize-ml:** Auto build experiment graph ([cc7c1b7](https://github.com/brysontang/crystallize/commit/cc7c1b78e2e16f4d962deac1ed302ebc13096168))


### Bug Fixes

* **crystallize-ml:** Allow decorated objects to be pickled ([654fc3b](https://github.com/brysontang/crystallize/commit/654fc3b8687f83ffa5b8e6b68bdfedea29bd4810))
* **crystallize-ml:** Pickle issue ([6830ac3](https://github.com/brysontang/crystallize/commit/6830ac3bbefeb6eaf5dc6d60c611d267d89f5374))

## [0.15.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.14.0...crystallize-ml@v0.15.0) (2025-07-21)


### Features

* **crystallize-ml:** Add logger to context ([86b3606](https://github.com/brysontang/crystallize/commit/86b3606d9766633f34dbfcbafb0f4e4c0fe67cf1))
* **crystallize-ml:** Add Output class and resume strategy ([60744bb](https://github.com/brysontang/crystallize/commit/60744bb610ed61547bdfef3aab651943f5bbe6ca))
* **crystallize-ml:** Introduce Artifact and ExperimentInput ([05ee063](https://github.com/brysontang/crystallize/commit/05ee063d9423c457d6fab4459e833e4109d55ea4))
* **crystallize-ml:** Refine resume logic ([ee6a787](https://github.com/brysontang/crystallize/commit/ee6a787e5326c6a2387be3f5ca713910272d8db2))


### Bug Fixes

* **crystallize-ml:** Resolve tests for new Artifact API ([02ec241](https://github.com/brysontang/crystallize/commit/02ec241efeb81cfe60a4c52f75b5622c5b765ca9))


### Documentation

* Auto-update generated API docs ([34375ed](https://github.com/brysontang/crystallize/commit/34375ed5296369127b220904cc4f09fdc6fa130c))
* **crystallize-ml:** Document Result.print_tree ([28bbf3a](https://github.com/brysontang/crystallize/commit/28bbf3aaa75dd0e0056fefe2ad94bf87a1a5225f))

## [0.14.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.13.0...crystallize-ml@v0.14.0) (2025-07-21)


### Features

* **crystallize-ml:** Flatten public api ([659ca6a](https://github.com/brysontang/crystallize/commit/659ca6a467bc890eb4e37572c0b6d3fe79b983bd))

## [0.13.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.12.0...crystallize-ml@v0.13.0) (2025-07-20)


### Features

* **crystallize-ml:** Improve ExperimentGraph and tests ([d532e2d](https://github.com/brysontang/crystallize/commit/d532e2da72da8f2ec820c498f57a66be87d2755c))

## [0.12.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.11.0...crystallize-ml@v0.12.0) (2025-07-20)


### Features

* **crystallize-extras:** Openai client ([57b7058](https://github.com/brysontang/crystallize/commit/57b70585d6c1c5646fae4e22ce36aef604e41473))
* **crystallize-extras:** Openai client ([1f6c10e](https://github.com/brysontang/crystallize/commit/1f6c10eedc86a6e6e423895cf0b7a0d3af407dbe))

## [0.11.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.10.0...crystallize-ml@v0.11.0) (2025-07-20)


### Features

* **crystallize-ml:** Add experiment name for artifact paths ([171c94f](https://github.com/brysontang/crystallize/commit/171c94f8028818021bf1ae2ce057da3318475296))
* **crystallize-ml:** Improve artifact datasource ([844bb00](https://github.com/brysontang/crystallize/commit/844bb0079bf62eb431ec9101c5d2814aafada2fa))


### Bug Fixes

* .apply adds the step setup to ctx ([171c94f](https://github.com/brysontang/crystallize/commit/171c94f8028818021bf1ae2ce057da3318475296))
* .apply adds the step setup to ctx ([f96ff2c](https://github.com/brysontang/crystallize/commit/f96ff2c2d55b57ed552aa096e56d910b723bf3f3))

## [0.10.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.9.0...crystallize-ml@v0.10.0) (2025-07-18)


### Features

* **crystallize-ml:** Make experiment methods stateless ([aad502d](https://github.com/brysontang/crystallize/commit/aad502d6922d4b6bcd57bb701c1aa7b59fb81c73))
* **crystallize-ml:** Make experiment state stateless ([0601416](https://github.com/brysontang/crystallize/commit/060141610423623fb6daf1721a2bb2c661d49ff7))
* **crystallize-ml:** Make experiment stateless ([f7c24a3](https://github.com/brysontang/crystallize/commit/f7c24a3e6a5ba612365690d9b20a39c830640434))
* **crystallize-ml:** Simplify resources with factories ([df5457b](https://github.com/brysontang/crystallize/commit/df5457bbcaaad1b3ebd19aaf6bfe2273c9a3c848))
* **crystallize-ml:** Stateless experiment runs ([caf9f1f](https://github.com/brysontang/crystallize/commit/caf9f1f7d15595da661037d75cd9c97672b14301))


### Bug Fixes

* **crystallize-ml:** Refine factory caching and injection ([0b3af92](https://github.com/brysontang/crystallize/commit/0b3af92ca18e5f5de3ff3b7e14a26eb01ff32a91))
* **crystallize-ml:** Refine logging and CLI output ([74bb33d](https://github.com/brysontang/crystallize/commit/74bb33d79f9a8f9990934001f4a5c1cc83accfd6))
* **crystallize-ml:** Restore dataclasses for results ([ac0fbfb](https://github.com/brysontang/crystallize/commit/ac0fbfb5bc02cbbb7809d52ecea0815cef389263))
* **crystallize-ml:** Set replicates default in apply ([fc3e75c](https://github.com/brysontang/crystallize/commit/fc3e75cd26a2eee2109daf440981fe9c1db27ddd))
* **crystallize-ml:** Update examples and tests ([32e35f4](https://github.com/brysontang/crystallize/commit/32e35f473ea1a7237e89e4fad69a38b94041bc93))


### Documentation

* Auto-update generated API docs ([f9b6cb9](https://github.com/brysontang/crystallize/commit/f9b6cb934e441a9ec2af24535cc31825162c36b2))

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
