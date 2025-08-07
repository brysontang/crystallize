## 0.25.0-alpha.0 (2025-08-01)

- Initial alpha release. Future changes may introduce breaking changes frequently until APIs stabilize.

## [0.26.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.25.0...crystallize-ml@v0.26.0) (2025-08-07)


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

## [0.25.1](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.25.0...crystallize-ml@v0.25.1) (2025-08-04)


### Bug Fixes

* Minor wording ([6ae4c3a](https://github.com/brysontang/crystallize/commit/6ae4c3abc3042c0c11e5bcd7694294593b4a8b31))
* Pypi deploy ([6c4b6ec](https://github.com/brysontang/crystallize/commit/6c4b6ec7993215917d7d91fd28208d46cf177dd6))

## [0.25.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.24.12...crystallize-ml@v0.25.0) (2025-08-04)


### Features

* Add artifact retention and caching ([fee3481](https://github.com/brysontang/crystallize/commit/fee3481fd6daf38c65b605d6586596974de2c71a))
* **cli:** Add treatment panel toggling and summary ([c30ea14](https://github.com/brysontang/crystallize/commit/c30ea142101da26a285b22cb037aff0632213558))
* **cli:** Add treatment panel toggling and summary ([70bdb1b](https://github.com/brysontang/crystallize/commit/70bdb1bde4a5ccfc8084bcafc338cd6741051073))
* **cli:** Open steps in external editor ([3e03304](https://github.com/brysontang/crystallize/commit/3e033040dbed0e063e74caad4bb6f0c9b5ba8b67))
* **cli:** Split experiment and treatment trees ([9081904](https://github.com/brysontang/crystallize/commit/908190486bab165e4445a8c684c279d2ee17191c))
* **cli:** Streamline run screen with cache toggling ([5fff14c](https://github.com/brysontang/crystallize/commit/5fff14c4b0fe8baba7bd0ce9c923a28439242377))
* **cli:** Style run screen layout ([f1a381d](https://github.com/brysontang/crystallize/commit/f1a381d86363ce8c23f6b0b5dd98a5fcbb78d52f))
* **crystallize-ml:** Add artifact retention and caching ([bcd5bdd](https://github.com/brysontang/crystallize/commit/bcd5bdd4365719f2bbf579de6fe61035a09bb6ba))
* **crystallize-ml:** Open steps in external editor ([9b1b447](https://github.com/brysontang/crystallize/commit/9b1b447de18c92003ce634faf58b25fec0b69102))
* Pipeline ETA and timing enhancements ([6285a71](https://github.com/brysontang/crystallize/commit/6285a7130af355f11b198d98cd8bff90dd6fffbf))


### Bug Fixes

* Added async ollama step ([57fe3b7](https://github.com/brysontang/crystallize/commit/57fe3b7222ee94ef9af477f6af417bbf9f963008))
* Added dotenv as dependency ([a7cc023](https://github.com/brysontang/crystallize/commit/a7cc02334c30a0bd7f443230acf6f55316d0725b))
* Cache state not sticking ([54b618f](https://github.com/brysontang/crystallize/commit/54b618f92fe4c6e22edc003a656eaf736cdbabb0))
* Can open experiment.yaml from runner screen ([a7cc023](https://github.com/brysontang/crystallize/commit/a7cc02334c30a0bd7f443230acf6f55316d0725b))
* Changelog ([9f47811](https://github.com/brysontang/crystallize/commit/9f47811539e97d96cf477e9a1939b10200b6bb8e))
* **cli:** Add load error screen ([4908076](https://github.com/brysontang/crystallize/commit/49080766604f47dc056d7a0fb4b5ec1b50cbd2b9))
* **cli:** Add summary tab and sidebar padding ([8f00650](https://github.com/brysontang/crystallize/commit/8f006503e1f1cf9665570187e0f79f46a8a5c6ae))
* **cli:** Address review feedback ([6408d5f](https://github.com/brysontang/crystallize/commit/6408d5fca5996614d7f0ec67697c1404035584fd))
* **cli:** Correct treatment colors and state parsing ([18fec0f](https://github.com/brysontang/crystallize/commit/18fec0febdcd6cf806f6c8068f88884276ab1360))
* **cli:** Ensure run screen opens summary tab ([ac46997](https://github.com/brysontang/crystallize/commit/ac46997d7ed160e0781d99ee42f81180f16ef71d))
* **cli:** Load historical treatment metrics and color cursor ([9b04660](https://github.com/brysontang/crystallize/commit/9b04660bff1831cb294294d97792b3f1dc5fca97))
* **cli:** Mark resumed experiments complete and update key bindings ([9adf12f](https://github.com/brysontang/crystallize/commit/9adf12f9d0c1e8228701644515608eefa515c15d))
* **cli:** Mark resumed experiments complete and update key bindings ([363a57c](https://github.com/brysontang/crystallize/commit/363a57cda32dc137505ebdf59703e5c6604edfd0))
* **cli:** Refine summary scope and keep pruned metrics ([48df400](https://github.com/brysontang/crystallize/commit/48df4001dfd368cbb2b2908afed60a10da7e1710))
* **cli:** Refine treatment panel internals ([b7dff5d](https://github.com/brysontang/crystallize/commit/b7dff5d9f44cc7dd5c7d322c0a7c9a984b037382))
* **cli:** Refine treatment toggling and summary\n\n- compute experiment strategy based on inactive treatments\n- strip version suffix when colouring summary rows\n- render context keys via apply_map and expose property\n- remove YAML parsing and harden tests\n\nfix(crystallize-ml): expose treatment apply_map ([1a6533a](https://github.com/brysontang/crystallize/commit/1a6533a42ad68d59e7b96cfbb55dc2efddcd47eb))
* **cli:** Reset run state per replicate ([748b218](https://github.com/brysontang/crystallize/commit/748b218540bbcef501839bacc6b7aa80d163ac18))
* **cli:** Show experiment name in run screen ([c256ebd](https://github.com/brysontang/crystallize/commit/c256ebdd3a3e3ee264bf1ae79eeb6d533aebb83c))
* **cli:** Stabilize run screen summary tab test ([f764f84](https://github.com/brysontang/crystallize/commit/f764f84201bc5dac1d5c73d7f9556d043b3d713f))
* Close run screen bug ([54b618f](https://github.com/brysontang/crystallize/commit/54b618f92fe4c6e22edc003a656eaf736cdbabb0))
* **crystallize-ml:** Clarify resume logic and async guidance ([4775879](https://github.com/brysontang/crystallize/commit/477587934ff1ff873c3a08380ec42c63ef4c3528))
* **crystallize-ml:** Clarify resume logic and async guidance ([5ef5a54](https://github.com/brysontang/crystallize/commit/5ef5a541e596b2e683e8baa5bef9630601b21349))
* **crystallize-ml:** Refine artifact pruning ([b067bc6](https://github.com/brysontang/crystallize/commit/b067bc641c517378a930072838eb1b6264672bd9))
* Docs ([9371948](https://github.com/brysontang/crystallize/commit/93719484a8498bfe3ce493635a821a333b4ee951))
* Docs ([9f47811](https://github.com/brysontang/crystallize/commit/9f47811539e97d96cf477e9a1939b10200b6bb8e))
* Error can be toggled to plain text ([5520e68](https://github.com/brysontang/crystallize/commit/5520e68eceab0c013819f3b31be47f02b371f1d3))
* Ignore timings for failed steps ([5b303ee](https://github.com/brysontang/crystallize/commit/5b303ee123c7b40ed0657d50e1c42e896448a765))
* Lint issue ([a7cc023](https://github.com/brysontang/crystallize/commit/a7cc02334c30a0bd7f443230acf6f55316d0725b))
* Opening in editor no longer opens the library ([a7cc023](https://github.com/brysontang/crystallize/commit/a7cc02334c30a0bd7f443230acf6f55316d0725b))
* Refine artifact pruning and metrics loading ([359ee94](https://github.com/brysontang/crystallize/commit/359ee94ba62c94e04a479b7da459b9bf42fb113a))
* Test coverage ([54b618f](https://github.com/brysontang/crystallize/commit/54b618f92fe4c6e22edc003a656eaf736cdbabb0))
* Use context emit callback directly ([88104b0](https://github.com/brysontang/crystallize/commit/88104b08f1d49e991c1c227fb89a1f773f090f37))
* Will resume if all treatments aren't selected ([dedd0f9](https://github.com/brysontang/crystallize/commit/dedd0f920fe8d5e65b242c5e6d206b7b2fcc5be9))


### Documentation

* Add architecture overview ([ccfd426](https://github.com/brysontang/crystallize/commit/ccfd4266958f027e3c5ec0b3eeee654de6d391f5))

## [0.24.12](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.24.11...crystallize-ml@v0.24.12) (2025-08-01)


### Bug Fixes

* Code coverage ([477b12f](https://github.com/brysontang/crystallize/commit/477b12f599e442c01a1d2497a5ca9dfb5f4b7f17))
* Linting errors ([477b12f](https://github.com/brysontang/crystallize/commit/477b12f599e442c01a1d2497a5ca9dfb5f4b7f17))
* Plugins now have a before_step ([dca6973](https://github.com/brysontang/crystallize/commit/dca69739cb487e93986f2684f00fb4c84037edfc))
* Textual now has a TextualLoggingPlugin that allows the user to d… ([882c35b](https://github.com/brysontang/crystallize/commit/882c35b97599f793a9111765611b0242b9e88f1f))
* Textual now has a TextualLoggingPlugin that allows the user to do ctx.logger ([dca6973](https://github.com/brysontang/crystallize/commit/dca69739cb487e93986f2684f00fb4c84037edfc))

## [0.24.11](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.24.10...crystallize-ml@v0.24.11) (2025-08-01)

### Bug Fixes

- Auto add matplotlib.use("Agg") for cli ([31ee0a0](https://github.com/brysontang/crystallize/commit/31ee0a0287ff7ef1b3be6fa987ed8cf3269e2076))
- Backwards compatibility for experiments root ([986de32](https://github.com/brysontang/crystallize/commit/986de320d621e153b475e3a124ef5516f450caf3))
- Increase_open_file_limit for umap errors ([31ee0a0](https://github.com/brysontang/crystallize/commit/31ee0a0287ff7ef1b3be6fa987ed8cf3269e2076))
- Pristine_stdio by default for textual ([b4152af](https://github.com/brysontang/crystallize/commit/b4152afae7d4a32349682d4cb98adfcb00df988a))
- Step has now includes code in hash ([986de32](https://github.com/brysontang/crystallize/commit/986de320d621e153b475e3a124ef5516f450caf3))
- Sub folder experiment data sources properly load ([7cf068e](https://github.com/brysontang/crystallize/commit/7cf068ee21a98e594bcc0424d6697a20951a19b1))
- Temp set xfail on seed tests ([5a9951f](https://github.com/brysontang/crystallize/commit/5a9951fedaf7e67ba4d5d2feea7e2e7563cd2a52))
- Tests ([cc14ead](https://github.com/brysontang/crystallize/commit/cc14ead6aa2375fd671be443b79b053788e35dbc))
- Textual\_\_log added to context to log ([b4152af](https://github.com/brysontang/crystallize/commit/b4152afae7d4a32349682d4cb98adfcb00df988a))

## [0.24.10](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.24.9...crystallize-ml@v0.24.10) (2025-07-30)

### Bug Fixes

- Added back hash error ([1a4a1ab](https://github.com/brysontang/crystallize/commit/1a4a1ab31c57a3a5788024dfa068a20c8a0d78d8))
- Limit size of metric table ([2187785](https://github.com/brysontang/crystallize/commit/218778594d903cda17051f3692a381b4b8e4e24e))

## [0.24.9](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.24.8...crystallize-ml@v0.24.9) (2025-07-30)

### Bug Fixes

- Artifact loader and writer use dill by default ([7c89642](https://github.com/brysontang/crystallize/commit/7c89642ed62a4c3b1fe51ce011f6a0f7577e2f80))

### Documentation

- **crystallize-ml:** Note treatment inheritance ([bf89dc1](https://github.com/brysontang/crystallize/commit/bf89dc1cd9ed703792bd7303322a62bbe1354379))

## [0.24.8](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.24.7...crystallize-ml@v0.24.8) (2025-07-29)

### Bug Fixes

- Crash on error ([64330bc](https://github.com/brysontang/crystallize/commit/64330bc108c572901aac24554e901f0a5ee5fe93))
- **crystallize-ml:** Correct artifact writer logic ([8bddb10](https://github.com/brysontang/crystallize/commit/8bddb105761983d1ef70522bb7c6656eb390c092))
- Implemented writer function for artifacts ([b14257e](https://github.com/brysontang/crystallize/commit/b14257ec0515187a17d8ce7382f6cc6303a4fdb9))

## [0.24.7](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.24.6...crystallize-ml@v0.24.7) (2025-07-29)

### Bug Fixes

- Added loading screen for loading experiments ([d371877](https://github.com/brysontang/crystallize/commit/d3718775d0f3a9dc59d7992ded5a4eccb289c7d1))
- Resume not being registered ([56d6a40](https://github.com/brysontang/crystallize/commit/56d6a4082366c720299a56df3b068cdc5384e29e))

## [0.24.6](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.24.5...crystallize-ml@v0.24.6) (2025-07-29)

### Bug Fixes

- Set default theme to nord ([93dd327](https://github.com/brysontang/crystallize/commit/93dd32793ac243375dc93fec472d838da7e119d0))
- Show details again ([93dd327](https://github.com/brysontang/crystallize/commit/93dd32793ac243375dc93fec472d838da7e119d0))

## [0.24.5](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.24.4...crystallize-ml@v0.24.5) (2025-07-28)

### Bug Fixes

- Before_step to plugins ([350211e](https://github.com/brysontang/crystallize/commit/350211eb4bc47987162557d535bb6053b271015f))
- Progress from steps updates ([24b6555](https://github.com/brysontang/crystallize/commit/24b655578d9c9a816a498ca2351d5c6bbec3d2f0))
- Progress from steps updates ([350211e](https://github.com/brysontang/crystallize/commit/350211eb4bc47987162557d535bb6053b271015f))
- Treatment state better displayed ([350211e](https://github.com/brysontang/crystallize/commit/350211eb4bc47987162557d535bb6053b271015f))
- Update CLI status plugin test ([491d6d4](https://github.com/brysontang/crystallize/commit/491d6d46628b0354a8b0b2708f9828da9c0dbd8c))

## [0.24.4](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.24.3...crystallize-ml@v0.24.4) (2025-07-28)

### Bug Fixes

- Final_final css fix ([68cc88b](https://github.com/brysontang/crystallize/commit/68cc88b9a2b9b09f43b8791e9022a4093d40f2ba))

## [0.24.3](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.24.2...crystallize-ml@v0.24.3) (2025-07-28)

### Bug Fixes

- Css issue in widget ([d63bad4](https://github.com/brysontang/crystallize/commit/d63bad4e9c768daa54bd64ef88e390f1f634073b))

## [0.24.2](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.24.1...crystallize-ml@v0.24.2) (2025-07-28)

### Bug Fixes

- Comment ([8f7b483](https://github.com/brysontang/crystallize/commit/8f7b48333183e088535b73d55e33dc2b46f96940))
- Put css in python file ([02bfd6b](https://github.com/brysontang/crystallize/commit/02bfd6b6164a43a3b6869ca1b67d743969a40c3a))

### Documentation

- Removed next steps on first cli ([a0450b8](https://github.com/brysontang/crystallize/commit/a0450b8ca72fe617ffd7869779862ca54bd59db1))

## [0.24.1](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.24.0...crystallize-ml@v0.24.1) (2025-07-28)

### Bug Fixes

- Clarification on running without cli ([94e18c4](https://github.com/brysontang/crystallize/commit/94e18c4b8939bcab57dc8c4ada2cbcad13b87a3a))

### Documentation

- Add CLI tutorial and sidebar ([e05063e](https://github.com/brysontang/crystallize/commit/e05063e450d788261938ea34ac3b400aefd6a8ff))
- **crystallize-ml:** Update getting started section ([cd8eb4d](https://github.com/brysontang/crystallize/commit/cd8eb4d21afd3cb3e386e4f28bbda1101a44b452))
- Expand CLI documentation ([8e3b0af](https://github.com/brysontang/crystallize/commit/8e3b0afb80d72c5d109172c275d6158d86099656))
- Expand cli tutorial and add graph example ([404a300](https://github.com/brysontang/crystallize/commit/404a300e235aebdd579e23b64667256812f21196))
- Minor tweaks to code ([7707042](https://github.com/brysontang/crystallize/commit/7707042f0f32ed11637e9c72d6c2cddc71a99b9f))
- Refine first CLI tutorial ([0fc3072](https://github.com/brysontang/crystallize/commit/0fc3072b7d23eedd5e0ef5d89f19f325641ab113))

## [0.24.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.23.0...crystallize-ml@v0.24.0) (2025-07-28)

### Features

- Added footer to run screens ([1d84026](https://github.com/brysontang/crystallize/commit/1d84026f662be76485b930d8b42d685fca351917))
- **cli:** Embed config editor in details panel ([b59e2e5](https://github.com/brysontang/crystallize/commit/b59e2e59bcafeb4c715e2844256797f2e9071973))
- **crystallize-ml:** Add code skeletons when editing config ([8856ef6](https://github.com/brysontang/crystallize/commit/8856ef61564f4e466aae7068e5b645caa9985659))
- **crystallize-ml:** Add interactive add nodes to config editor ([33f8e6a](https://github.com/brysontang/crystallize/commit/33f8e6a95006409e18b473277bdeb16e65196c56))
- **crystallize-ml:** Add YAML config editor ([ab89586](https://github.com/brysontang/crystallize/commit/ab895869455714b592c2a995f9db35b8d9ebc9e8))
- **crystallize-ml:** Refine modal styles ([db82b34](https://github.com/brysontang/crystallize/commit/db82b3429297b2bdd5223afe74c643d75bbc1d2b))

### Bug Fixes

- A and c for close and open all ([1d84026](https://github.com/brysontang/crystallize/commit/1d84026f662be76485b930d8b42d685fca351917))
- **cli:** Postpone annotations in config widget ([327c673](https://github.com/brysontang/crystallize/commit/327c673be15721d2f2adab152be8d56530ef7576))
- Command palette shows again ([9133cb4](https://github.com/brysontang/crystallize/commit/9133cb4d51114799940705f05ce0c89440399dee))
- Edit config no longer has border ([e177a69](https://github.com/brysontang/crystallize/commit/e177a6912c33d8b126826cdd90c165fc4f9ff19a))
- Enter on leaf node edits it ([62ff82c](https://github.com/brysontang/crystallize/commit/62ff82ce52ba24dd67f62c3b49598aae5f32c370))
- ExperimentInput now takes in a datasource instead of an artifact ([e177a69](https://github.com/brysontang/crystallize/commit/e177a6912c33d8b126826cdd90c165fc4f9ff19a))
- Flat lists now don't have children ([d41069c](https://github.com/brysontang/crystallize/commit/d41069cd37f880b63716376dc849db6f0db8da94))
- Footer commands now consistent for runner flow ([844be98](https://github.com/brysontang/crystallize/commit/844be98e08d548aa7785b5f230e3c276a8db4458))
- Footer order ([1d84026](https://github.com/brysontang/crystallize/commit/1d84026f662be76485b930d8b42d685fca351917))
- Hypotheses.py -&gt; verifiers.py ([ea86db8](https://github.com/brysontang/crystallize/commit/ea86db8f3d0ccad28e405f203bcc43b9521cefc6))
- Hypotheses.py -&gt; verifiers.py ([7a9e508](https://github.com/brysontang/crystallize/commit/7a9e508425582ac58a5c4d90dabd85a0950d1e82))
- Issue if opening crystallize with no experiments ([6cc2cc2](https://github.com/brysontang/crystallize/commit/6cc2cc205dc650af22704e363a9ec7d0a5b83c8a))
- Issue where certain adds didn't work/exist ([0d09c65](https://github.com/brysontang/crystallize/commit/0d09c6589bc54cf08bd3b0a86a284eb3b50b7bb9))
- Minor style changes ([1e66b9a](https://github.com/brysontang/crystallize/commit/1e66b9a09a203b73e167e6516df05674d8f63edd))
- N is now new experiment ([1d84026](https://github.com/brysontang/crystallize/commit/1d84026f662be76485b930d8b42d685fca351917))
- New exp bug ([b3f78f0](https://github.com/brysontang/crystallize/commit/b3f78f058bb83eab535df1639b43703ce36a542d))
- Ordering values works now ([50ae448](https://github.com/brysontang/crystallize/commit/50ae44865563d4958f78589ac8f54258b5bfed67))
- Removed plain text toggle from run ([62ff82c](https://github.com/brysontang/crystallize/commit/62ff82ce52ba24dd67f62c3b49598aae5f32c370))
- Rendering issue ([38e02ad](https://github.com/brysontang/crystallize/commit/38e02ad208c88b80e7f9dbe78d910122f8d5fd42))
- Setting value in config ([1d84026](https://github.com/brysontang/crystallize/commit/1d84026f662be76485b930d8b42d685fca351917))
- Treatment format ([24c0f85](https://github.com/brysontang/crystallize/commit/24c0f85ef86add79230bf7873a98a84685f06877))
- Treatment format ([ea86db8](https://github.com/brysontang/crystallize/commit/ea86db8f3d0ccad28e405f203bcc43b9521cefc6))
- Treatment format ([7a9e508](https://github.com/brysontang/crystallize/commit/7a9e508425582ac58a5c4d90dabd85a0950d1e82))
- Unused test file ([d50ef60](https://github.com/brysontang/crystallize/commit/d50ef60f5f07c35e5ce9ba51cf0e1aa96476f181))
- Verifier ([62ff82c](https://github.com/brysontang/crystallize/commit/62ff82ce52ba24dd67f62c3b49598aae5f32c370))

## [0.23.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.22.0...crystallize-ml@v0.23.0) (2025-07-27)

### Features

- **crystallize-ml:** Add CLI presentation controls ([8c19568](https://github.com/brysontang/crystallize/commit/8c19568ea09387e1edee5716878921c4fe612a86))
- **crystallize-ml:** Add plain text toggle for run logs ([efc2b44](https://github.com/brysontang/crystallize/commit/efc2b444a96825c370d1b1b0fb48744b0c7389e9))
- **crystallize-ml:** Show outputs in tree on create ([7162080](https://github.com/brysontang/crystallize/commit/7162080af1f97fccf83fa4faab86d6a3c0081251))
- Improve details panel and replicates input ([be5b085](https://github.com/brysontang/crystallize/commit/be5b08500d3e134242062eb25178a443d04d1447))

### Bug Fixes

- Buttons on bottom of run no longer stack ([3224ca9](https://github.com/brysontang/crystallize/commit/3224ca9a7277e07af6ab1c70409c97cef8cc584a))
- **cli:** Allow selecting outputs with space ([9b6ae95](https://github.com/brysontang/crystallize/commit/9b6ae9508df51107109e75837510dca2e0a8209d))
- Crash if not deletable ([b89ec5a](https://github.com/brysontang/crystallize/commit/b89ec5aafa85a5b76a08a13257905cb29bac07e2))
- **crystallize-ml:** Refine cli presentation ([12c2ad7](https://github.com/brysontang/crystallize/commit/12c2ad7c91dc91ac2c15862eeadc0231e07153bd))
- Don't close creator on error ([5d19a5c](https://github.com/brysontang/crystallize/commit/5d19a5cc0d755c99f3a394e5f90af4732f0a1c91))
- Enter runs experiment ([83af0c6](https://github.com/brysontang/crystallize/commit/83af0c63a0a799fd526647a594edcab042bdd928))
- Failing test ([effe292](https://github.com/brysontang/crystallize/commit/effe292f20957e94900141fa2524ae903146dc70))
- Made two columns ([5cb562d](https://github.com/brysontang/crystallize/commit/5cb562dccb6719332fee066ecb1f35ccfaeadc4e))
- Plain text toggle works ([3224ca9](https://github.com/brysontang/crystallize/commit/3224ca9a7277e07af6ab1c70409c97cef8cc584a))
- Removed [dim] ([b89ec5a](https://github.com/brysontang/crystallize/commit/b89ec5aafa85a5b76a08a13257905cb29bac07e2))
- Run and replicate button now aligned vertically ([6df5ebd](https://github.com/brysontang/crystallize/commit/6df5ebd97f79fcd9d44ddcd4dee907bd617b76a3))
- Use enter to select input in creator ([9250b27](https://github.com/brysontang/crystallize/commit/9250b27ec07c9c348367c17731249f6aa8736a48))

### Documentation

- Note replicates editing in selection screen ([202d665](https://github.com/brysontang/crystallize/commit/202d66571be6ad50a305d6ca72a10a569cdd422c))

## [0.22.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.21.0...crystallize-ml@v0.22.0) (2025-07-27)

### Features

- **cli:** Use selection lists for experiment setup ([58052e4](https://github.com/brysontang/crystallize/commit/58052e451f0f2ed227c8a019af167bf6df4d2cb7))
- **crystallize-ml:** Add search and run controls to selection screen ([08f6e2a](https://github.com/brysontang/crystallize/commit/08f6e2a2dbabc9b2f4c2d80ceec836b35e250704))
- **crystallize-ml:** Combine run setup screens ([e0dd2b2](https://github.com/brysontang/crystallize/commit/e0dd2b2157c8c0c000367d9a514e3a8a80d184d8))
- **crystallize-ml:** Graph inputs in CLI create ([d02e4b6](https://github.com/brysontang/crystallize/commit/d02e4b643aaa0751266f239f8b3f3ca95c96cacf))
- **crystallize-ml:** Move experiment selection to screen ([b4e1749](https://github.com/brysontang/crystallize/commit/b4e17492a808c4b5efe7ca6c9e1040cee016f4d1))
- **crystallize-ml:** Recursive graph loading ([5f2abdf](https://github.com/brysontang/crystallize/commit/5f2abdf0a805bd253d431282c143c1648fcc7d7f))
- **crystallize-ml:** Recursive graph loading ([5fcfb48](https://github.com/brysontang/crystallize/commit/5fcfb48de0c6cd64c641b82a5d68ee229d3cbd56))
- **crystallize-ml:** Refine experiment creator ui ([a0f1549](https://github.com/brysontang/crystallize/commit/a0f15491a8189480bfec5ec0c5f1cc4cfdb173c6))
- **crystallize-ml:** Show load errors in cli ([fe062ea](https://github.com/brysontang/crystallize/commit/fe062ea7a1b82cb1dd8309191e6f84033a02044d))
- **crystallize-ml:** Support tuple metrics in pipeline steps ([b92304f](https://github.com/brysontang/crystallize/commit/b92304f69f5938d24c181892169882f85ce7f62e))
- **crystallize-ml:** Support tuple returns in pipeline steps ([8e62d60](https://github.com/brysontang/crystallize/commit/8e62d60454abf8205a0aeadf9d4eee8834b6b329))
- **crystallize-ml:** Use yaml-based discovery ([34c7911](https://github.com/brysontang/crystallize/commit/34c7911dc476ba8feaf47d36407a36bda38b0758))
- **crystallize-ml:** Validate outputs and pickle loaders ([3e5642a](https://github.com/brysontang/crystallize/commit/3e5642ac2ce5660a4b8737962a45abd69925b88c))
- Display CLI load errors ([be44d7c](https://github.com/brysontang/crystallize/commit/be44d7ca6c1e656cfea55df68332f63de8f29c51))
- Improve YAML artifact mapping ([f583542](https://github.com/brysontang/crystallize/commit/f5835422780fc6a23bac47e9f9508a21c9601a6c))

### Bug Fixes

- Added summary button to runner ([75b14f2](https://github.com/brysontang/crystallize/commit/75b14f2ec3a31e1ca38e28e695567cf0a7281d82))
- Cli refresh updates import ([aee7a11](https://github.com/brysontang/crystallize/commit/aee7a11cf63b1583be29f987db2be18ad711130d))
- **cli:** Require strategy selection ([da6ce61](https://github.com/brysontang/crystallize/commit/da6ce61d5dc83c283a0eefa1be020eab1b5642f1))
- Correctly hide/display input experiments ([7de6fe0](https://github.com/brysontang/crystallize/commit/7de6fe0c3186a5379bbeb622b9977150ddb079e7))
- **crystallize-ml:** Ensure ExperimentInput for upstream refs ([f0bd67b](https://github.com/brysontang/crystallize/commit/f0bd67bc683ebc1fc9fbbc2e6f7cbba443025139))
- **crystallize-ml:** Show feedback when run strategy missing ([3732137](https://github.com/brysontang/crystallize/commit/3732137dbba19b80e47c5e6b662c277e76847ead))
- **crystallize-ml:** Treat baseline-named treatment as baseline ([6ba1ff1](https://github.com/brysontang/crystallize/commit/6ba1ff1c09cc2dd87a797354933dc0781506a34d))
- Default to graph view ([1c56315](https://github.com/brysontang/crystallize/commit/1c563156776c8311932045c25b609951a348bef4))
- Delete data only visible when on resume mode ([f5e6257](https://github.com/brysontang/crystallize/commit/f5e6257a2d8220a2e54dc3e7f719e0c5b37706a8))
- Dill issue ([3229589](https://github.com/brysontang/crystallize/commit/322958956f8c5b37b58d5dd0d164c974e434cfb8))
- Experiment not being able to be run ([e0556b0](https://github.com/brysontang/crystallize/commit/e0556b018072c7988cc2f043d9fa1bd0abd5c589))
- From_yaml reloads module ([1f179b1](https://github.com/brysontang/crystallize/commit/1f179b1c68c8a8f1ceecfe97084e4822409aed05))
- If inputs, make experiment graph instead ([7de6fe0](https://github.com/brysontang/crystallize/commit/7de6fe0c3186a5379bbeb622b9977150ddb079e7))
- Linting error ([98b74e6](https://github.com/brysontang/crystallize/commit/98b74e6c0b5b691be11b6b2d39555c63df1cc32a))
- Provide examples is checkbox again ([5540967](https://github.com/brysontang/crystallize/commit/5540967e6d4c88c5799f36b4fde61fa7a617ca8e))
- Put rerun first in order ([88aff59](https://github.com/brysontang/crystallize/commit/88aff5928f368cd860a3bc73086e70fa71dc7e1f))
- Show traceback of error ([aee7a11](https://github.com/brysontang/crystallize/commit/aee7a11cf63b1583be29f987db2be18ad711130d))

## [0.21.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.20.2...crystallize-ml@v0.21.0) (2025-07-26)

### Features

- **crystallize-ml:** Add experiment creator in CLI ([2840cec](https://github.com/brysontang/crystallize/commit/2840cec090b7234682f3a29ac1c726f64a3a8c10))
- **crystallize-ml:** Add fluent experiment builder ([36b02b9](https://github.com/brysontang/crystallize/commit/36b02b9934d340d47db47eb90567c1d1a788315c))
- **crystallize-ml:** Add folder-based YAML loader ([ed657bf](https://github.com/brysontang/crystallize/commit/ed657bfa20d256bed524c55a9905e1afaec1bd83))
- **crystallize-ml:** Auto-validate on run ([d3613b8](https://github.com/brysontang/crystallize/commit/d3613b8f9ce794e8d01d0f8efdab699140eeaabe))
- **crystallize-ml:** Infer experiment graph deps automatically ([f39cd57](https://github.com/brysontang/crystallize/commit/f39cd57a81004da41a6ce46316ed477a753c38d7))
- **crystallize-ml:** Infer experiment graph deps automatically ([88a40a7](https://github.com/brysontang/crystallize/commit/88a40a796ea234e22e65e800613f1362725f2dea))
- **crystallize-ml:** Show hypothesis results in summary ([26e4818](https://github.com/brysontang/crystallize/commit/26e4818647644aa12709c0783e911d746aa3ae58))
- **crystallize-ml:** Update folder YAML loader ([0d4ab93](https://github.com/brysontang/crystallize/commit/0d4ab93ad711b87697e10a07c006e1efb5cd34ee))
- Experiment sets default plugins on initialize ([68c7a55](https://github.com/brysontang/crystallize/commit/68c7a553b260cb3b873c4999695cc18e96eaa35b))

### Bug Fixes

- Added data folder to git ignore ([014d63b](https://github.com/brysontang/crystallize/commit/014d63b151ffe5ad0e583fee54f978c318e39831))
- Artifact default loader no longer causes pickle error ([fc0dc6e](https://github.com/brysontang/crystallize/commit/fc0dc6ebcc1edee432eb2a559f8c75ed85226f93))
- Better error handling for writer widget ([ca21c7c](https://github.com/brysontang/crystallize/commit/ca21c7cdaf4e60682d61466919cba021238d3cac))
- Can have more replicates than data source ([ca21c7c](https://github.com/brysontang/crystallize/commit/ca21c7cdaf4e60682d61466919cba021238d3cac))
- Changed default artifacts folder to ./data ([d45d51f](https://github.com/brysontang/crystallize/commit/d45d51ffec18953746aa7d0619062c0889d3f9d3))
- **crystallize-ml:** Restore hypothesis decorator behavior ([d0f57a7](https://github.com/brysontang/crystallize/commit/d0f57a713df3f0cc8650cec1c512a754b58b88e7))
- From_yaml for experiment now checks for Artifacts from signature ([fc0dc6e](https://github.com/brysontang/crystallize/commit/fc0dc6ebcc1edee432eb2a559f8c75ed85226f93))
- Issues with running async experiments with verifiers ([42ebe1f](https://github.com/brysontang/crystallize/commit/42ebe1f22fe74854ebad8de93cd5b463e51cf561))
- New line between tables ([6b5cd90](https://github.com/brysontang/crystallize/commit/6b5cd904d19ff189106a4e6bae0c88ef70fe5b25))
- No longer check replicates mismatch, % handles this ([b75138a](https://github.com/brysontang/crystallize/commit/b75138a31755e90549b343ced92e72dbd97be2fe))
- Test ([0748575](https://github.com/brysontang/crystallize/commit/0748575731aab92edab8792075304a5c1c327fe7))
- Treatment now object instead of array ([c8ccf69](https://github.com/brysontang/crystallize/commit/c8ccf698fe895d2d3df03d0e8d82af5372a0f8c6))
- Update tests and docs ([95c2f4e](https://github.com/brysontang/crystallize/commit/95c2f4e407267816899900cb44f550bd2f0ccd8a))
- Verifier and hypothesis are now pickleable ([1c68a45](https://github.com/brysontang/crystallize/commit/1c68a45f2c9f10cdf108a5dc20c69c19cc5bb916))

### Documentation

- Auto-update generated API docs ([972d199](https://github.com/brysontang/crystallize/commit/972d199494d680a83a46e5144ce933cbc76998a3))

## [0.20.2](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.20.1...crystallize-ml@v0.20.2) (2025-07-24)

### Bug Fixes

- Can use q to quit cli screen ([6356344](https://github.com/brysontang/crystallize/commit/6356344fdef60da0c214b32066d83940cb7a6133))
- **cli:** Avoid duplicate status plugin injection ([4c4932c](https://github.com/brysontang/crystallize/commit/4c4932c33d05f2457f32abe036a3ad22c16c8a41))
- **crystallize-ml:** Reset step states each treatment ([2407af2](https://github.com/brysontang/crystallize/commit/2407af2c3001f29a2b5c93fa5225aecba69c8f2b))

## [0.20.1](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.20.0...crystallize-ml@v0.20.1) (2025-07-24)

### Bug Fixes

- Pypi build ([7b679b1](https://github.com/brysontang/crystallize/commit/7b679b110a9ce3d4fc3a42f42e158db3dd58597c))

## [0.20.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.19.1...crystallize-ml@v0.20.0) (2025-07-24)

### Features

- **crystallize-ml:** Add description param ([01fb8a2](https://github.com/brysontang/crystallize/commit/01fb8a27773156c177ab7250a079290e0bf1f95f))
- **crystallize-ml:** Add interactive CLI ([3d1e8af](https://github.com/brysontang/crystallize/commit/3d1e8afbf21ead49ea14653e873a2e5546a7e3af))
- **crystallize-ml:** Rebuild interactive cli using textual ([c2bc34f](https://github.com/brysontang/crystallize/commit/c2bc34f38f7ef4892bb548f5e277ac39a20872b8))
- **crystallize-ml:** Refactor CLI to Textual app ([f864d55](https://github.com/brysontang/crystallize/commit/f864d5587516430d961c172d9af5f70f366b02fa))
- Display current experiment if running experiment graph ([bb55d47](https://github.com/brysontang/crystallize/commit/bb55d47d923d7303b421aa251a121b8ac34d7e13))
- Random ascii art ([4b51cab](https://github.com/brysontang/crystallize/commit/4b51cab6f78170eebd90009a0fe2edea8d628405))

### Bug Fixes

- Cleaned up ui ([6fa524e](https://github.com/brysontang/crystallize/commit/6fa524e56e68017effaa920d43123da57ab8d037))
- Cli for better delete and folder management ([c3e9733](https://github.com/brysontang/crystallize/commit/c3e97334b1889dd62b8c2e982d798fb01d5e67ad))
- Cli running graph ([f20a2a9](https://github.com/brysontang/crystallize/commit/f20a2a90b2256f71e41cb0ffb59ef30a8a69c429))
- Ctrl+c goes back ([79b8a8d](https://github.com/brysontang/crystallize/commit/79b8a8df3c4ecdd4106d6cc18d7308079b2cf430))
- Experiment graphs now have names ([f20a2a9](https://github.com/brysontang/crystallize/commit/f20a2a90b2256f71e41cb0ffb59ef30a8a69c429))
- Experiment selection not working ([839ad16](https://github.com/brysontang/crystallize/commit/839ad161c65e33b48e3a85fe0bf1bc083f7f2540))
- Failing tests ([e091fc1](https://github.com/brysontang/crystallize/commit/e091fc182a8a25e81d2e8c56e1e664dea4dd4542))
- Logs not print ([79b8a8d](https://github.com/brysontang/crystallize/commit/79b8a8df3c4ecdd4106d6cc18d7308079b2cf430))
- Missing tests ([821e51b](https://github.com/brysontang/crystallize/commit/821e51bb1e787cd036e5cffd80ca965de36d49cc))
- Progress updates from experiment graph ([0c1c46c](https://github.com/brysontang/crystallize/commit/0c1c46cd8ecd736551ded9f34261a91ebdf68699))
- Show error in thread ([a00f6ff](https://github.com/brysontang/crystallize/commit/a00f6ff560cd94a80ba2d31207e465c904867551))
- Summary only shows tables that have data ([8f0315a](https://github.com/brysontang/crystallize/commit/8f0315ae72ef61593e0f0815be7fba8c6118a590))
- Summary screen back ([4b51cab](https://github.com/brysontang/crystallize/commit/4b51cab6f78170eebd90009a0fe2edea8d628405))
- Test warnings ([821e51b](https://github.com/brysontang/crystallize/commit/821e51bb1e787cd036e5cffd80ca965de36d49cc))

## [0.19.1](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.19.0...crystallize-ml@v0.19.1) (2025-07-23)

### Bug Fixes

- **crystallize-ml:** Restore sync wrappers and async support ([f9dc241](https://github.com/brysontang/crystallize/commit/f9dc2418a5e5f7123b5f0d7ca5598ebd2632762e))
- **crystallize-ml:** Simplify async execution ([9b2ca76](https://github.com/brysontang/crystallize/commit/9b2ca76d7ec581d030a50d08844ab45b536cfd15))

### Documentation

- **crystallize-ml:** Document async pipeline steps ([afab757](https://github.com/brysontang/crystallize/commit/afab757194ddfb278a0f2b502400bc0333e6f7ab))

## [0.19.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.18.0...crystallize-ml@v0.19.0) (2025-07-23)

### Features

- **crystallize-ml:** Add per-experiment replicate counts and fix DAG execution ([db13a4c](https://github.com/brysontang/crystallize/commit/db13a4cbdaf9b51c62618f63f274380cd0f1fdc6))

### Documentation

- Add best practices guide ([ece0573](https://github.com/brysontang/crystallize/commit/ece057343bd99d731c76184d7686de3d8d2e6c58))
- **crystallize-ml:** Add advanced caching and seed plugin guides ([eb0ca47](https://github.com/brysontang/crystallize/commit/eb0ca47c80f6fd143e8d34e3ffe2d3f3ecc9e466))

## [0.18.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.17.1...crystallize-ml@v0.18.0) (2025-07-23)

### Features

- **crystallize-ml:** Load metrics on resumed skip ([2440f0e](https://github.com/brysontang/crystallize/commit/2440f0e8e2e1f23aa41ad7a0f6a0fd7557c6537a))

### Bug Fixes

- Looks for the specific file needed ([0da24b7](https://github.com/brysontang/crystallize/commit/0da24b7e471bb49295b1d357b1950d7a92c5c56e))

## [0.17.1](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.17.0...crystallize-ml@v0.17.1) (2025-07-23)

### Bug Fixes

- **crystallize-ml:** Handle artifact datasource ([54ae23d](https://github.com/brysontang/crystallize/commit/54ae23d797f9864b2eee6cd0ab550f3107b314ae))

## [0.17.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.16.0...crystallize-ml@v0.17.0) (2025-07-22)

### Features

- Add apply mode and optional components ([c886505](https://github.com/brysontang/crystallize/commit/c886505d50b4f355611d5286f1b6278a479590d9))
- Add caching and provenance ([5ed6e67](https://github.com/brysontang/crystallize/commit/5ed6e671cb7d03d0e1afac08822f32addb6bdb4e))
- Add context parameter injection ([447cd61](https://github.com/brysontang/crystallize/commit/447cd614d3b91dfa48ad5766e9ef9ae41154f199))
- Add deterministic auto seeding ([c510312](https://github.com/brysontang/crystallize/commit/c510312bb0b5d4bc53ad27c0e9cfd26d719ec3df))
- Add ResourceHandle and improve step init ([63ce75e](https://github.com/brysontang/crystallize/commit/63ce75ed4b84db2e589824dadfe1b1b046cec9e0))
- **crystallize-extras:** Add Ollama client step ([9c5e91e](https://github.com/brysontang/crystallize/commit/9c5e91e6eb00b77b9e2a1b0a4a76bbe2e77be98f))
- **crystallize-extras:** Openai client ([57b7058](https://github.com/brysontang/crystallize/commit/57b70585d6c1c5646fae4e22ce36aef604e41473))
- **crystallize-extras:** Openai client ([1f6c10e](https://github.com/brysontang/crystallize/commit/1f6c10eedc86a6e6e423895cf0b7a0d3af407dbe))
- **crystallize-ml:** Add experiment name for artifact paths ([171c94f](https://github.com/brysontang/crystallize/commit/171c94f8028818021bf1ae2ce057da3318475296))
- **crystallize-ml:** Add logger to context ([86b3606](https://github.com/brysontang/crystallize/commit/86b3606d9766633f34dbfcbafb0f4e4c0fe67cf1))
- **crystallize-ml:** Add Output class and resume strategy ([60744bb](https://github.com/brysontang/crystallize/commit/60744bb610ed61547bdfef3aab651943f5bbe6ca))
- **crystallize-ml:** Add plugin lifecycle to apply ([fb0e288](https://github.com/brysontang/crystallize/commit/fb0e28861cc4dc0b97da34151e8a3821931cd93f))
- **crystallize-ml:** Add ResourceHandle utility ([07e5102](https://github.com/brysontang/crystallize/commit/07e5102ea050ef42f56abee056518579c48bf4ff))
- **crystallize-ml:** Apply uses full lifecycle ([9c58a07](https://github.com/brysontang/crystallize/commit/9c58a074b1ccc84dc75f1e2c30d74f30bc2e1657))
- **crystallize-ml:** Auto build experiment graph ([cc7c1b7](https://github.com/brysontang/crystallize/commit/cc7c1b78e2e16f4d962deac1ed302ebc13096168))
- **crystallize-ml:** Chain experiments via artifact datasource ([7c718a6](https://github.com/brysontang/crystallize/commit/7c718a6bea6b67fdeae7519302906ca04913ed6b))
- **crystallize-ml:** Flatten public api ([659ca6a](https://github.com/brysontang/crystallize/commit/659ca6a467bc890eb4e37572c0b6d3fe79b983bd))
- **crystallize-ml:** Improve artifact datasource ([844bb00](https://github.com/brysontang/crystallize/commit/844bb0079bf62eb431ec9101c5d2814aafada2fa))
- **crystallize-ml:** Improve ExperimentGraph and tests ([d532e2d](https://github.com/brysontang/crystallize/commit/d532e2da72da8f2ec820c498f57a66be87d2755c))
- **crystallize-ml:** Introduce Artifact and ExperimentInput ([05ee063](https://github.com/brysontang/crystallize/commit/05ee063d9423c457d6fab4459e833e4109d55ea4))
- **crystallize-ml:** Make experiment methods stateless ([aad502d](https://github.com/brysontang/crystallize/commit/aad502d6922d4b6bcd57bb701c1aa7b59fb81c73))
- **crystallize-ml:** Make experiment state stateless ([0601416](https://github.com/brysontang/crystallize/commit/060141610423623fb6daf1721a2bb2c661d49ff7))
- **crystallize-ml:** Make experiment stateless ([f7c24a3](https://github.com/brysontang/crystallize/commit/f7c24a3e6a5ba612365690d9b20a39c830640434))
- **crystallize-ml:** Polish artifact datasource ([c784139](https://github.com/brysontang/crystallize/commit/c7841392dd84dd378d189f70a4f63ee0fc454695))
- **crystallize-ml:** Refine resume logic ([ee6a787](https://github.com/brysontang/crystallize/commit/ee6a787e5326c6a2387be3f5ca713910272d8db2))
- **crystallize-ml:** Return artifact paths ([0077c1e](https://github.com/brysontang/crystallize/commit/0077c1ee159c97dcdf2f75a2ec0703d33b0500ed))
- **crystallize-ml:** Simplify resources with factories ([df5457b](https://github.com/brysontang/crystallize/commit/df5457bbcaaad1b3ebd19aaf6bfe2273c9a3c848))
- **crystallize-ml:** Stateless experiment runs ([caf9f1f](https://github.com/brysontang/crystallize/commit/caf9f1f7d15595da661037d75cd9c97672b14301))
- Support multiple hypotheses ([27ed2e3](https://github.com/brysontang/crystallize/commit/27ed2e3971b777ccc7e5f1cb176f784b6bc6d717))

### Bug Fixes

- .apply adds the step setup to ctx ([171c94f](https://github.com/brysontang/crystallize/commit/171c94f8028818021bf1ae2ce057da3318475296))
- .apply adds the step setup to ctx ([f96ff2c](https://github.com/brysontang/crystallize/commit/f96ff2c2d55b57ed552aa096e56d910b723bf3f3))
- **crystallize-ml:** Allow decorated objects to be pickled ([654fc3b](https://github.com/brysontang/crystallize/commit/654fc3b8687f83ffa5b8e6b68bdfedea29bd4810))
- **crystallize-ml:** Ollama base_url -&gt; host ([10be1d1](https://github.com/brysontang/crystallize/commit/10be1d1e3a113a5107e26a5583e89af2ad4fa26b))
- **crystallize-ml:** Ollama base_url -&gt; host ([adc3319](https://github.com/brysontang/crystallize/commit/adc33194c42d623498401e947e6b79b37379663f))
- **crystallize-ml:** Pickle issue ([6830ac3](https://github.com/brysontang/crystallize/commit/6830ac3bbefeb6eaf5dc6d60c611d267d89f5374))
- **crystallize-ml:** Refine factory caching and injection ([0b3af92](https://github.com/brysontang/crystallize/commit/0b3af92ca18e5f5de3ff3b7e14a26eb01ff32a91))
- **crystallize-ml:** Refine logging and CLI output ([74bb33d](https://github.com/brysontang/crystallize/commit/74bb33d79f9a8f9990934001f4a5c1cc83accfd6))
- **crystallize-ml:** Resolve tests for new Artifact API ([02ec241](https://github.com/brysontang/crystallize/commit/02ec241efeb81cfe60a4c52f75b5622c5b765ca9))
- **crystallize-ml:** Restore dataclasses for results ([ac0fbfb](https://github.com/brysontang/crystallize/commit/ac0fbfb5bc02cbbb7809d52ecea0815cef389263))
- **crystallize-ml:** Set replicates default in apply ([fc3e75c](https://github.com/brysontang/crystallize/commit/fc3e75cd26a2eee2109daf440981fe9c1db27ddd))
- **crystallize-ml:** Update examples and tests ([32e35f4](https://github.com/brysontang/crystallize/commit/32e35f473ea1a7237e89e4fad69a38b94041bc93))
- Crystallize.core now exports classes ([d7456be](https://github.com/brysontang/crystallize/commit/d7456beb4955c06474485c5685857b98f4bd7618))
- Double import ([41a5a2d](https://github.com/brysontang/crystallize/commit/41a5a2d45cbdbed177099cfae3d6a38e5a9abb74))

### Documentation

- Add core concepts overview ([042bc8d](https://github.com/brysontang/crystallize/commit/042bc8dbb3ac78c116b8d05fe8c937abbbb5617c))
- Add FAQ document ([e15f7c5](https://github.com/brysontang/crystallize/commit/e15f7c5a98e01965b49895e9c2b7f6d37f095cd4))
- Add framework extension guide ([73cb6bb](https://github.com/brysontang/crystallize/commit/73cb6bbd383e5aae0d26f6c2b2fb725afeafc769))
- Add full workflow tutorial ([fa372b6](https://github.com/brysontang/crystallize/commit/fa372b6b715f2e27e8333fa7617683ecf32e1538))
- Add optimization tutorial and reference ([262ce0e](https://github.com/brysontang/crystallize/commit/262ce0ed67e6614e51b96c20c211c3df41252401))
- Add parallelism explanation ([e3590f0](https://github.com/brysontang/crystallize/commit/e3590f0f6dfdcdf6f434519753e9460681d021c2))
- Add reproducibility section ([b61d62e](https://github.com/brysontang/crystallize/commit/b61d62e472a0a056ca436cb5ded0293284b74afb))
- Add retrospective changelogs for main and extras packages ([ad715ae](https://github.com/brysontang/crystallize/commit/ad715ae23e0e00c17bf86f77f1ce808a855fc7e7))
- Added code2prompt command ([81fb94f](https://github.com/brysontang/crystallize/commit/81fb94f43e573a7706349f44a79bdf531e996774))
- Auto-update generated API docs ([34375ed](https://github.com/brysontang/crystallize/commit/34375ed5296369127b220904cc4f09fdc6fa130c))
- Auto-update generated API docs ([6302344](https://github.com/brysontang/crystallize/commit/63023449b48c5ae050ff782af1ad7453b6edb5de))
- Auto-update generated API docs ([3e7bcb1](https://github.com/brysontang/crystallize/commit/3e7bcb16930b45493ea89f3186bc862eb251b095))
- Auto-update generated API docs ([f9b6cb9](https://github.com/brysontang/crystallize/commit/f9b6cb934e441a9ec2af24535cc31825162c36b2))
- Auto-update generated API docs ([8b71015](https://github.com/brysontang/crystallize/commit/8b71015d434a2ebed636c03cac34aa92786d6b84))
- **crystallize-ml:** Document Result.print_tree ([28bbf3a](https://github.com/brysontang/crystallize/commit/28bbf3aaa75dd0e0056fefe2ad94bf87a1a5225f))
- Document context injection ([6699023](https://github.com/brysontang/crystallize/commit/6699023e79d5d62af9ff8b7a47da19a11208b935))
- Fix glossary link for custom steps ([d430522](https://github.com/brysontang/crystallize/commit/d430522a2869f026044496cc95d8bd86007ff582))
- Update reference docs and generation workflow ([10bcec4](https://github.com/brysontang/crystallize/commit/10bcec461da38eb09cd2cfbcdf0d36be1f03ad3d))

## [0.16.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.15.0...crystallize-ml@v0.16.0) (2025-07-22)

### Features

- **crystallize-ml:** Auto build experiment graph ([cc7c1b7](https://github.com/brysontang/crystallize/commit/cc7c1b78e2e16f4d962deac1ed302ebc13096168))

### Bug Fixes

- **crystallize-ml:** Allow decorated objects to be pickled ([654fc3b](https://github.com/brysontang/crystallize/commit/654fc3b8687f83ffa5b8e6b68bdfedea29bd4810))
- **crystallize-ml:** Pickle issue ([6830ac3](https://github.com/brysontang/crystallize/commit/6830ac3bbefeb6eaf5dc6d60c611d267d89f5374))

## [0.15.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.14.0...crystallize-ml@v0.15.0) (2025-07-21)

### Features

- **crystallize-ml:** Add logger to context ([86b3606](https://github.com/brysontang/crystallize/commit/86b3606d9766633f34dbfcbafb0f4e4c0fe67cf1))
- **crystallize-ml:** Add Output class and resume strategy ([60744bb](https://github.com/brysontang/crystallize/commit/60744bb610ed61547bdfef3aab651943f5bbe6ca))
- **crystallize-ml:** Introduce Artifact and ExperimentInput ([05ee063](https://github.com/brysontang/crystallize/commit/05ee063d9423c457d6fab4459e833e4109d55ea4))
- **crystallize-ml:** Refine resume logic ([ee6a787](https://github.com/brysontang/crystallize/commit/ee6a787e5326c6a2387be3f5ca713910272d8db2))

### Bug Fixes

- **crystallize-ml:** Resolve tests for new Artifact API ([02ec241](https://github.com/brysontang/crystallize/commit/02ec241efeb81cfe60a4c52f75b5622c5b765ca9))

### Documentation

- Auto-update generated API docs ([34375ed](https://github.com/brysontang/crystallize/commit/34375ed5296369127b220904cc4f09fdc6fa130c))
- **crystallize-ml:** Document Result.print_tree ([28bbf3a](https://github.com/brysontang/crystallize/commit/28bbf3aaa75dd0e0056fefe2ad94bf87a1a5225f))

## [0.14.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.13.0...crystallize-ml@v0.14.0) (2025-07-21)

### Features

- **crystallize-ml:** Flatten public api ([659ca6a](https://github.com/brysontang/crystallize/commit/659ca6a467bc890eb4e37572c0b6d3fe79b983bd))

## [0.13.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.12.0...crystallize-ml@v0.13.0) (2025-07-20)

### Features

- **crystallize-ml:** Improve ExperimentGraph and tests ([d532e2d](https://github.com/brysontang/crystallize/commit/d532e2da72da8f2ec820c498f57a66be87d2755c))

## [0.12.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.11.0...crystallize-ml@v0.12.0) (2025-07-20)

### Features

- **crystallize-extras:** Openai client ([57b7058](https://github.com/brysontang/crystallize/commit/57b70585d6c1c5646fae4e22ce36aef604e41473))
- **crystallize-extras:** Openai client ([1f6c10e](https://github.com/brysontang/crystallize/commit/1f6c10eedc86a6e6e423895cf0b7a0d3af407dbe))

## [0.11.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.10.0...crystallize-ml@v0.11.0) (2025-07-20)

### Features

- **crystallize-ml:** Add experiment name for artifact paths ([171c94f](https://github.com/brysontang/crystallize/commit/171c94f8028818021bf1ae2ce057da3318475296))
- **crystallize-ml:** Improve artifact datasource ([844bb00](https://github.com/brysontang/crystallize/commit/844bb0079bf62eb431ec9101c5d2814aafada2fa))

### Bug Fixes

- .apply adds the step setup to ctx ([171c94f](https://github.com/brysontang/crystallize/commit/171c94f8028818021bf1ae2ce057da3318475296))
- .apply adds the step setup to ctx ([f96ff2c](https://github.com/brysontang/crystallize/commit/f96ff2c2d55b57ed552aa096e56d910b723bf3f3))

## [0.10.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.9.0...crystallize-ml@v0.10.0) (2025-07-18)

### Features

- **crystallize-ml:** Make experiment methods stateless ([aad502d](https://github.com/brysontang/crystallize/commit/aad502d6922d4b6bcd57bb701c1aa7b59fb81c73))
- **crystallize-ml:** Make experiment state stateless ([0601416](https://github.com/brysontang/crystallize/commit/060141610423623fb6daf1721a2bb2c661d49ff7))
- **crystallize-ml:** Make experiment stateless ([f7c24a3](https://github.com/brysontang/crystallize/commit/f7c24a3e6a5ba612365690d9b20a39c830640434))
- **crystallize-ml:** Simplify resources with factories ([df5457b](https://github.com/brysontang/crystallize/commit/df5457bbcaaad1b3ebd19aaf6bfe2273c9a3c848))
- **crystallize-ml:** Stateless experiment runs ([caf9f1f](https://github.com/brysontang/crystallize/commit/caf9f1f7d15595da661037d75cd9c97672b14301))

### Bug Fixes

- **crystallize-ml:** Refine factory caching and injection ([0b3af92](https://github.com/brysontang/crystallize/commit/0b3af92ca18e5f5de3ff3b7e14a26eb01ff32a91))
- **crystallize-ml:** Refine logging and CLI output ([74bb33d](https://github.com/brysontang/crystallize/commit/74bb33d79f9a8f9990934001f4a5c1cc83accfd6))
- **crystallize-ml:** Restore dataclasses for results ([ac0fbfb](https://github.com/brysontang/crystallize/commit/ac0fbfb5bc02cbbb7809d52ecea0815cef389263))
- **crystallize-ml:** Set replicates default in apply ([fc3e75c](https://github.com/brysontang/crystallize/commit/fc3e75cd26a2eee2109daf440981fe9c1db27ddd))
- **crystallize-ml:** Update examples and tests ([32e35f4](https://github.com/brysontang/crystallize/commit/32e35f473ea1a7237e89e4fad69a38b94041bc93))

### Documentation

- Auto-update generated API docs ([f9b6cb9](https://github.com/brysontang/crystallize/commit/f9b6cb934e441a9ec2af24535cc31825162c36b2))

## [0.9.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.8.1...crystallize-ml@v0.9.0) (2025-07-18)

### Features

- Add ResourceHandle and improve step init ([63ce75e](https://github.com/brysontang/crystallize/commit/63ce75ed4b84db2e589824dadfe1b1b046cec9e0))
- **crystallize-ml:** Add ResourceHandle utility ([07e5102](https://github.com/brysontang/crystallize/commit/07e5102ea050ef42f56abee056518579c48bf4ff))

### Documentation

- Auto-update generated API docs ([8b71015](https://github.com/brysontang/crystallize/commit/8b71015d434a2ebed636c03cac34aa92786d6b84))

## [0.8.1](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.8.0...crystallize-ml@v0.8.1) (2025-07-18)

### Bug Fixes

- **crystallize-ml:** Ollama base_url -&gt; host ([10be1d1](https://github.com/brysontang/crystallize/commit/10be1d1e3a113a5107e26a5583e89af2ad4fa26b))
- **crystallize-ml:** Ollama base_url -&gt; host ([adc3319](https://github.com/brysontang/crystallize/commit/adc33194c42d623498401e947e6b79b37379663f))

## [0.8.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.7.0...crystallize-ml@v0.8.0) (2025-07-18)

### Features

- **crystallize-ml:** Add plugin lifecycle to apply ([fb0e288](https://github.com/brysontang/crystallize/commit/fb0e28861cc4dc0b97da34151e8a3821931cd93f))
- **crystallize-ml:** Apply uses full lifecycle ([9c58a07](https://github.com/brysontang/crystallize/commit/9c58a074b1ccc84dc75f1e2c30d74f30bc2e1657))

## [0.7.0](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.6.2...crystallize-ml@v0.7.0) (2025-07-18)

### Features

- **crystallize-extras:** Add Ollama client step ([9c5e91e](https://github.com/brysontang/crystallize/commit/9c5e91e6eb00b77b9e2a1b0a4a76bbe2e77be98f))
- **crystallize-ml:** Chain experiments via artifact datasource ([7c718a6](https://github.com/brysontang/crystallize/commit/7c718a6bea6b67fdeae7519302906ca04913ed6b))
- **crystallize-ml:** Polish artifact datasource ([c784139](https://github.com/brysontang/crystallize/commit/c7841392dd84dd378d189f70a4f63ee0fc454695))
- **crystallize-ml:** Return artifact paths ([0077c1e](https://github.com/brysontang/crystallize/commit/0077c1ee159c97dcdf2f75a2ec0703d33b0500ed))

## [0.6.2](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.6.1...crystallize-ml@v0.6.2) (2025-07-15)

### Bug Fixes

- Crystallize.core now exports classes ([d7456be](https://github.com/brysontang/crystallize/commit/d7456beb4955c06474485c5685857b98f4bd7618))
- Double import ([41a5a2d](https://github.com/brysontang/crystallize/commit/41a5a2d45cbdbed177099cfae3d6a38e5a9abb74))

### Documentation

- Add full workflow tutorial ([fa372b6](https://github.com/brysontang/crystallize/commit/fa372b6b715f2e27e8333fa7617683ecf32e1538))
- Added code2prompt command ([81fb94f](https://github.com/brysontang/crystallize/commit/81fb94f43e573a7706349f44a79bdf531e996774))

## [0.6.1](https://github.com/brysontang/crystallize/compare/crystallize-ml@v0.6.0...crystallize-ml@v0.6.1) (2025-07-15)

### Documentation

- Add retrospective changelogs for main and extras packages ([ad715ae](https://github.com/brysontang/crystallize/commit/ad715ae23e0e00c17bf86f77f1ce808a855fc7e7))
- Update reference docs and generation workflow ([10bcec4](https://github.com/brysontang/crystallize/commit/10bcec461da38eb09cd2cfbcdf0d36be1f03ad3d))

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
