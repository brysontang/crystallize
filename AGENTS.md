# AGENTS.md

This document provides instructions and context for automated agents (Codex, Copilot, etc.) working within the Crystallize repository.

---

## 📖 Ethos & Philosophy

Crystallize is built around rigorous, reproducible, and intuitive data science experimentation. When making changes or contributing code, always prioritize:

- **Clarity**: Code should clearly communicate intent and implementation.
- **Reproducibility**: Ensure deterministic outcomes, clear provenance, and robust caching.
- **Minimalism**: Keep abstractions simple, intuitive, and easy to use without overcomplicating.
- **Scientific Rigor**: Align closely with best practices in experimental science, emphasizing statistical verification and methodological correctness.

---

## 🧭 Scope

Instructions here apply to all files and subdirectories rooted in the directory containing this AGENTS.md file, unless overridden by a more deeply nested AGENTS.md file.

---

## 🚦 Coding Conventions

- **Formatting**: Strictly follow PEP 8 standards. Use `black` and `isort` to auto-format imports and code.
- **Type Hints**: Always include clear and explicit type hints. Use `mypy` for static type checking.
- **Imports**: Only explicit imports; never use wildcard imports.
- **Naming**:

  - Classes: `PascalCase`
  - Functions, methods, variables: `snake_case`
  - Constants: `UPPER_CASE`

- **Error Handling**: Use explicit, informative, and custom-defined exceptions to provide clear debugging and user experience.

---

## 📂 Project Structure

The repository structure is intentionally simple and clear:

```
crystallize/
├── crystallize/
│   ├── core/        # Core abstractions: minimal, abstract definitions only
│   ├── steps/       # Minimal illustrative step implementations
│   └── experiment.py
├── tests/
│   └── test_*.py
└── examples/
    ├── minimal_experiment/
    │   └── *.py
    └── csv_pipeline_example/
        └── *.py
```

Maintain this clarity and simplicity. Clearly separate abstract core functionality from concrete example implementations.

---

## 📝 PR Messages

Automated agents generating PR messages should follow these structured guidelines:

- Provide a clear and concise explanation of both **what** changed and **why**.
- Follow this structured format:

```
### Summary

Clearly describe the motivation and objectives for this PR.

### Changes

- Bullet points highlighting key changes.

### Testing & Verification

Explain exactly how the changes were tested and provide clear verification steps.

### Notes

Additional context or important details not covered elsewhere.
```

---

## ✅ Checks and Validation

Before finalizing any PR, run and ensure passing results from:

- Unit tests:

```bash
pixi run test
```

- Formatting, linting, and static checks:

```bash
pixi run lint
```

These checks are mandatory for all contributions.

---

## ⚠️ Resolving Conflicts

In case of conflicting instructions:

1. Instructions directly provided by developers/users in prompts have the highest precedence.
2. Instructions in deeper nested AGENTS.md files override this document.
