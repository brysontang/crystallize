# AGENTS.md

This document provides instructions for automated agents (Codex, Copilot, etc.) working within this repository.

## 🧭 Scope

Instructions here apply to all files and subdirectories rooted in the directory containing this AGENTS.md file, unless overridden by a more deeply nested AGENTS.md file.

---

## 🚦 Coding Conventions

- **Formatting**: Follow PEP 8 standards. Use `black` and `isort` to auto-format imports and code.
- **Type Hints**: Always include type hints. Use `mypy` for static analysis.
- **Imports**: Explicit imports only (no wildcard imports).
- **Naming**:

  - Classes: `PascalCase`
  - Functions, methods, variables: `snake_case`
  - Constants: `UPPER_CASE`

---

## 📂 Project Structure

The repository follows this general layout:

```
crystallize/
├── crystallize/
│   ├── core/        # Core abstractions
│   ├── steps/       # Pipeline step implementations
│   └── experiment.py
├── tests/
│   └── test_*.py
└── examples/
    └── *.py
```

Respect this structure and organize new files accordingly.

---

## 🔍 PR Messages

Automated agents generating PR messages should follow these guidelines:

- Clearly summarize the **what** and **why** of the changes.
- Use the format:

```
### Summary

Brief summary of the changes.

### Changes

- Bullet list of notable changes.

### Testing

Describe how changes were tested and verification instructions.

### Notes

Optional additional context or notes.
```

---

## ✅ Checks and Validation

Before finalizing a PR:

- Run all provided tests using `pytest`:

```bash
pixi run test
```

- Ensure linting and formatting pass:

```bash
pixi run lint
```

- Run coverage report, make sure it's at 80%:

```bash
pixi run cov
```

All checks must pass prior to PR submission.

## Testing Philosophy for Codex

The primary objective of testing within Codex is to ensure robust, reliable code through thoughtful, targeted stress testing. Our philosophy prioritizes meaningful coverage over exhaustive, redundant testing. To achieve this:

1. **Focus on Edge Cases:**

   - Prioritize edge cases and boundary conditions that users are realistically likely to encounter.
   - Validate inputs, handle unusual or unexpected user behaviors gracefully, and ensure the application remains stable under atypical scenarios.

2. **Pragmatic Coverage:**

   - Aim for clarity and precision rather than excessive coverage.
   - Tests should clearly reflect plausible use-cases rather than contrived or improbable scenarios.

3. **Stress Realism, Not Perfection:**

   - Emphasize realistic stress conditions rather than theoretical extremes.
   - The goal is resilient code, effectively tested against plausible scenarios, not absolute perfection in every hypothetical case.

4. **Maintain Readability and Intent:**

   - Tests should be clear and self-explanatory, reflecting the intent and logic behind them.
   - Prioritize tests that enhance maintainability and long-term understandability of the codebase.

Following this approach ensures Codex remains dependable, user-centric, and maintainable, without unnecessary overhead or complexity in testing.

---

## ⚠️ Conflicts

In case of conflicting instructions:

1. Developer/user instructions in prompt take precedence.
2. Instructions in deeper nested AGENTS.md files take precedence over this file.
