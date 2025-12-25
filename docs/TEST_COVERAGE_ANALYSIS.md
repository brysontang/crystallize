# Test Coverage Analysis

This document provides an analysis of the test coverage in the crystallize-ml codebase and proposes areas for improvement.

## Current Testing Infrastructure

- **Test Framework**: pytest with pytest-asyncio (async support) and hypothesis (property-based testing)
- **Coverage Tool**: pytest-cov with Codecov integration
- **Coverage Targets**: 80% patch coverage, 90% project coverage
- **Test Files**: 43 test files in `tests/` + 4 in `extras/crystallize-extras/tests/`
- **Total Test LOC**: ~7,500+ lines of tests

## Coverage Gap Analysis

### 1. Core Library (`crystallize/`) - Missing Dedicated Tests

| Module | File | Status | Priority |
|--------|------|--------|----------|
| experiments | `experiment_builder.py` | Partially tested via `test_experiment.py` | Medium |
| experiments | `aggregation.py` | No dedicated tests | **High** |
| experiments | `run_results.py` | No dedicated tests | Medium |
| plugins | `artifacts.py` (load_metrics, load_all_metrics) | Partial coverage | **High** |

#### Specific Gaps in `aggregation.py`

The `ResultAggregator` class (89 lines) handles critical aggregation logic:
- `aggregate_results()` - Collects baseline/treatment samples, seeds, provenance, errors
- `build_result()` - Constructs the final `Result` object with provenance

**Recommended tests**:
- Test aggregation with multiple replicates
- Test error handling when some replicates fail
- Test provenance building with various seed configurations
- Test empty results aggregation

#### Specific Gaps in `plugins/artifacts.py`

The `load_metrics()` and `load_all_metrics()` functions need coverage for:
- Version discovery and selection
- Baseline vs treatment metric loading
- Missing file handling
- Cross-version treatment loading

### 2. CLI (`cli/`) - Missing Test Coverage

| Module | File | Lines | Status | Priority |
|--------|------|-------|--------|----------|
| screens | `delete_data.py` | 56 | No tests | **High** |
| screens | `load_error.py` | 33 | No tests | Medium |
| screens | `loading.py` | 23 | No tests | Low |
| screens | `selection_screens.py` | 58 | No tests | Medium |
| core | `app.py` | 151 | Minimal tests | **High** |
| core | `errors.py` | 33 | No tests | Medium |
| core | `yaml_edit.py` | 82 | No tests | **High** |
| core | `main.py` | Entrypoint | No tests | Low |

#### Specific Gaps in `delete_data.py` (`ConfirmScreen`)

This modal screen handles dangerous file deletion confirmation:
- Keybindings: y/n/Escape/ctrl+c
- Button actions: Yes/No
- Empty path list display

**Recommended tests**:
- Test keyboard bindings trigger correct actions
- Test button presses dismiss with correct result
- Test empty paths list displays "(Nothing selected)"
- Test focus behavior on mount

#### Specific Gaps in `yaml_edit.py`

Three important functions without tests:
1. `find_treatment_line()` - Finds line number of treatment in YAML
2. `ensure_new_treatment_placeholder()` - Adds placeholder for new treatment
3. `find_treatment_apply_line()` - Finds specific key within treatment block

**Recommended tests**:
- Test line finding in various YAML structures
- Test placeholder insertion at correct position
- Test handling of malformed YAML
- Test edge cases (empty file, no treatments block)

#### Specific Gaps in `app.py` (`CrystallizeApp`)

The main application class needs tests for:
- `_apply_overrides()` - matplotlib backend switching
- `increase_open_file_limit()` - resource limit handling
- `run()` function - CLI argument parsing
- `--serve` mode behavior

### 3. Edge Case and Error Handling Coverage

#### Missing Exception Path Tests

1. **`cli/errors.py`** - `format_load_error()` handles multiple exception types:
   - `yaml.YAMLError` - Invalid YAML
   - `FileNotFoundError` - Missing referenced files
   - `AttributeError` - Invalid module references
   - `KeyError` - Missing configuration keys
   - Generic exceptions

   Only tested implicitly - needs dedicated unit tests.

2. **`crystallize/utils/exceptions.py`** - Custom exceptions need validation tests

3. **Plugin error propagation** - Some error paths in plugins may be untested

### 4. Integration Test Gaps

#### Async Execution Paths

The `AsyncExecution` plugin has some coverage but could use:
- Tests with failing async steps
- Concurrent treatment execution tests
- Resource cleanup after async failures

#### Plugin Lifecycle

More tests needed for full plugin lifecycle:
- `before_replicate` / `after_replicate` hooks
- Error handling in plugin hooks
- Plugin interaction (multiple plugins together)

### 5. Property-Based Testing Opportunities

The codebase uses Hypothesis but could expand property-based tests:

1. **Pipeline signature generation** - Verify signatures are deterministic
2. **Treatment application** - Verify treatments apply consistently
3. **Metrics aggregation** - Verify aggregation preserves data integrity
4. **YAML parsing** - Verify round-trip consistency

### 6. Extras Package (`crystallize-extras`)

| Module | Test File | Status |
|--------|-----------|--------|
| ollama_step | test_ollama_step.py | Has tests |
| openai_step | test_openai_step.py | Has tests |
| vllm_step | test_vllm_step.py | Has tests |
| ray_plugin | test_ray_execution.py | Has tests |

**Gap**: These are mostly integration tests requiring external services. Mock-based unit tests would improve CI reliability.

## Recommended Test Improvements (Prioritized)

### High Priority

1. **Add `test_aggregation.py`**
   - Test `ResultAggregator.aggregate_results()` with various input scenarios
   - Test `ResultAggregator.build_result()` provenance building
   - ~50-100 lines of tests

2. **Add `test_delete_data.py`**
   - Test `ConfirmScreen` keyboard bindings and button actions
   - Test empty/populated path lists
   - ~40-60 lines of tests

3. **Add `test_yaml_edit.py`**
   - Test all three functions with various YAML structures
   - Test edge cases (empty files, malformed YAML)
   - ~80-120 lines of tests

4. **Add `test_cli_errors.py`**
   - Test `format_load_error()` for all exception types
   - ~30-50 lines of tests

5. **Expand `test_artifacts.py`**
   - Add tests for `load_metrics()` and `load_all_metrics()`
   - Test version discovery and cross-version loading
   - ~60-80 lines of tests

### Medium Priority

6. **Add `test_app.py`**
   - Test `CrystallizeApp` initialization and overrides
   - Test file limit adjustments
   - Mock-based CLI argument parsing tests

7. **Add `test_load_error.py`**
   - Test `LoadErrorScreen` modal behavior
   - Test keybindings and dismissal

8. **Add `test_selection_screens.py`**
   - Test `ActionableSelectionList` selection behavior
   - Test `SingleSelectionList` single-selection enforcement

9. **Expand `test_experiment_builder.py`**
   - Dedicated tests for builder pattern (currently in test_experiment.py)
   - Test all builder methods
   - Test validation errors

### Low Priority

10. **Add `test_loading_screen.py`**
    - Simple screen with minimal logic

11. **Add integration tests for CLI main()**
    - Test full CLI invocation with mocked TUI

## Test Quality Improvements

### Current Strengths

- Good coverage of core `Experiment` class (~80 tests in test_experiment.py)
- Thorough pipeline and step testing
- Proper async test support with pytest-asyncio
- Good error scenario coverage for core experiment execution

### Suggested Improvements

1. **Add docstrings to test functions** - Many tests lack descriptions
2. **Group related tests in classes** - Improve organization in larger files
3. **Add parametrized edge case tests** - Use `@pytest.mark.parametrize` more
4. **Add performance regression tests** - Mark slow tests, add benchmarks
5. **Improve fixture reuse** - More shared fixtures in conftest.py

## Estimated Coverage Impact

Implementing the high-priority recommendations would add approximately:
- 300-400 lines of new tests
- Coverage increase of ~3-5% (estimated)
- Better error path coverage

## Conclusion

The crystallize-ml codebase has solid test coverage for core functionality (~90% target), but has gaps in:
1. CLI screens and utilities (delete, load error, yaml edit)
2. Result aggregation logic
3. Artifact loading/metrics utilities
4. Error formatting and exception handling

Addressing these gaps will improve reliability, especially for the CLI interface and edge case handling.
