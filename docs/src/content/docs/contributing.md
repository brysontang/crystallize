---
title: Contributing to Crystallize
description: How to contribute to Crystallize
---

First off, thank you for considering contributing to Crystallize! We welcome contributions of all kinds, from bug reports and documentation improvements to new features and architectural suggestions. Every contribution helps make Crystallize a better tool for everyone.

This project adheres to a philosophy of clarity, reproducibility, and scientific rigor. Please keep these principles in mind as you propose changes.

## Getting Started: Setting Up Your Environment

To contribute code, you'll need to set up a local development environment. Crystallize uses `pixi` to manage dependencies and environments, which ensures a consistent setup for all contributors.

1. **Prerequisite**: Ensure you have [pixi](https://pixi.sh) installed on your system.

2. **Fork and Clone the Repository**:

- Fork the official [Crystallize repository](https://github.com/brysontang/crystallize) on GitHub.
- Clone your fork to your local machine:

```bash
git clone https://github.com/<YOUR-USERNAME>/crystallize.git
cd crystallize
```

3. **Install Dependencies**:

Use `pixi` to install all required dependencies as specified in the `pixi.toml` file. This command creates a virtual environment in the `.pixi` directory and installs everything needed for development and testing.

```bash
pixi install
```

## Running Tests and Checks

To maintain code quality and stability, we require that all contributions pass our suite of tests and linting checks.

- **Run Unit Tests**: Execute the full test suite using pytest.

```bash
pixi run test
```

- **Run Linting and Formatting Checks**: We use `ruff` for linting and formatting.

```bash
pixi run lint
```

Please ensure both commands run successfully without errors before submitting a pull request.

## How to Contribute

### Code Contributions

We follow a standard GitHub workflow for code changes.

1. **Create a Branch**: From the main branch, create a new feature branch for your changes. Please use a descriptive name.

```bash
# Example: git checkout -b feature/new-statistical-verifier

# Example: git checkout -b fix/cache-invalidation-bug

git checkout -b <type>/<short-description>
```

2. **Make Your Changes**: Write the code for your new feature or bug fix.

3. **Add Tests**: All new features must be accompanied by tests. Bug fixes should ideally include a test that exposes the bug and verifies the fix. Tests are located in the `/tests` directory.

4. **Validate**: Run the tests and linter to ensure your changes haven't introduced any issues.

```bash
pixi run test
pixi run lint
```

5. **Commit and Push**: Commit your changes with a clear, descriptive commit message and push them to your forked repository.

6. **Open a Pull Request**: Navigate to the Crystallize repository on GitHub and open a pull request from your feature branch to the main branch.

### Documentation Contributions

Our documentation is built with [Starlight](https://starlight.astro.build) and the source files are located in the `/docs` directory. We welcome improvements, corrections, and new content.

- **Editing Pages**: Most pages are standard Markdown (`.md`) files. You can edit them directly.
- **Structure**: The documentation follows the [Diátaxis](https://diataxis.fr) framework. Please try to place new content in the appropriate section (Tutorial, How-To, Reference, or Explanation).
- **Submitting Changes**: For small changes like typos or clarifications, you can use the "Edit this page" link on the documentation site. For larger changes, please follow the same PR process as for code contributions.

### Pull Request Guidelines

To help us review your PR efficiently, please ensure the following:

- **Clear Title**: The PR title should be a concise summary of the change (e.g., "Feat: Add support for Chi-squared verifier").
- **Detailed Description**: Fill out the PR description template to explain the **what** and **why** of your changes. A good description helps the reviewer understand your thought process.

A good PR description looks like this:

```markdown
### Summary

Clearly describe the motivation and objectives for this PR. For example: "This PR introduces a new `ChiSquaredVerifier` to enable goodness-of-fit tests within hypotheses, addressing issue #42."

### Changes

- Added `crystallize/verifiers/chi_squared.py` with the new verifier logic.
- Created `tests/test_chi_squared_verifier.py` with unit tests covering key scenarios.
- Updated documentation in `docs/reference/verifiers.md` to include the new class.
```

### Testing & Verification

Explain exactly how the changes were tested. "All new and existing unit tests pass via `pixi run test`. Manually verified the verifier's output against a known example from a statistics textbook."

### Developer FAQ & Common Pitfalls

#### **Q: I'm getting a `ContextMutationError`. Why?**

A: Crystallize uses an immutable `FrozenContext` to ensure reproducibility and prevent side effects. This error means a `PipelineStep` or `Treatment` tried to change an existing key in the context.

- **Incorrect**: `ctx["learning_rate"] = 0.001` (This will fail if `learning_rate` already exists)
- **Correct**: `ctx.add("new_learning_rate", 0.001)` (_Only add new, non-conflicting keys_)

Treatments should only **add** new parameters to the context for downstream steps to use.

#### **Q: My tests are failing due to cache inconsistencies. What should I do?**

A: The cache lives in the `.cache/` directory. If you suspect it's stale or causing issues during development, you can safely delete it:

```bash
rm -rf .cache/
```

#### **Q: Why is my experiment running slowly with the `ThreadPoolExecutor`?**

A: Python's Global Interpreter Lock (GIL) means the `ThreadPoolExecutor` provides limited benefit for CPU-bound tasks (like heavy numerical computation), as only one thread can execute Python bytecode at a time.

- For **I/O-bound** steps (e.g., waiting for API calls, reading from disk), use the default `"thread"` executor.
- For **CPU-bound** steps (e.g., complex simulations, training a model), use the
  `ParallelExecution` plugin with the `"process"` executor:

```python
Experiment(
    plugins=[ParallelExecution(executor_type="process")]
)
```

Remember that all data passed between processes must be "picklable".

## Code of Conduct

All contributors are expected to adhere to our Code of Conduct. Please be respectful and constructive in all interactions.
