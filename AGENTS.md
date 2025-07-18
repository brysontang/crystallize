# AGENTS.md

This document provides simplified instructions for automated agents (e.g., Codex, Copilot) working in the Crystallize repository. Follow these to ensure consistent, high-quality contributions.

---

## 📖 Ethos & Philosophy

Crystallize prioritizes reproducible, intuitive data science experiments. When contributing:

- Ensure clarity, minimalism, and scientific rigor.
- Keep changes holistic: Update code, docs, examples, and tests together for consistency.

---

## 🧭 Scope

Applies to the entire repo unless overridden by a nested AGENTS.md. Docs and tests are split: Core library (crystallize/) vs. extras (extras/crystallize-extras/)—do not mix them.

---

## 🚦 Coding Conventions

- **Formatting**: PEP 8 via `black` and `isort`.
- **Type Hints**: Always use explicit hints; check with `mypy`.
- **Imports**: Explicit only; no wildcards.
- **Naming**: Classes `PascalCase`; functions/vars `snake_case`; constants `UPPER_CASE`.
- **Error Handling**: Use custom exceptions for clear messaging.

---

## 📂 Project Structure

Keep it simple:

- `crystallize/`: Core code (abstractions in `core/`, steps in `steps/`).
- `tests/`: Unit tests (separate core vs. extras).
- `examples/`: Illustrative examples (update with changes).
- `extras/crystallize-extras/`: Optional plugins (separate tests/docs).

---

## 🛠️ Contribution Workflow

For any change:

1. **Update Docs & Examples**: Ensure all docs (e.g., README, tutorials) and examples reflect the change for consistency, update astro.config.mjs for new docs.
2. **Run & Fix Tests**: Execute `pixi run test`. Fix broken code first; only update tests if they're outdated (don't refactor tests to mask code issues).
3. **Add New Tests**: Write tests for new features/behaviors to capture them fully.
4. **Validate**: Run `pixi run lint` and `pixi run test`—all must pass.

---

## 📝 Commit Messages

Use Conventional Commits for semantic versioning (pre-alpha: avoid major bumps).

- Types: `chore` (no bump), `docs` (no bump), `feat` (minor), `fix` (patch). Avoid `feat!` or `fix!` (major).
- Scopes for monorepo: `feat(crystallize-ml):` for core changes; `feat(crystallize-extras):` for extras. If both: Use footers like `feat(crystallize-ml): ...` and `feat(crystallize-extras): ...` in the body.
- Example: `feat(crystallize-ml): add new pipeline step\n\nfix(crystallize-extras): update ray plugin`.

---

## 📝 PR Messages

Structure as:

```
### Summary
[Motivation and objectives.]

### Changes
- [Key changes.]

### Testing & Verification
[How tested; verification steps.]

### Notes
[Additional context.]
```

---

## ⚠️ Resolving Conflicts

Prompt instructions > nested AGENTS.md > this file.
