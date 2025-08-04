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

- **Formatting**: PEP 8 via `ruff`.
- **Type Hints**: Always use explicit hints; check with `mypy`.
- **Imports**: Explicit only; no wildcards.
- **Naming**: Classes `PascalCase`; functions/vars `snake_case`; constants `UPPER_CASE`.
- **Error Handling**: Use custom exceptions for clear messaging.

---

## 📂 Project Structure

Keep it simple:

- `crystallize/`: Core code (abstractions in `core/`, steps in `steps/`).
- `cli/`: CLI code (abstractions in `core/`, steps in `steps/`).
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
5. **Run Coverage**: Run `pixi run cov` to check coverage (codecov requires a 90% project coverage for the PR to pass).
6. **Run Diff Coverage**: Run `pixi run diff-cov` to check diff coverage (codecov requires a 80% patch coverage for the PR to pass).

---

## 🤖 Automated Agent Instructions

### 1. Consult ARCHITECTURE.md First

Before making any changes or writing any plans, thoroughly read:

```
docs/architecture/ARCHITECTURE.md
```

This provides critical context about module responsibilities, relationships, and overall architecture.
If unclear, explicitly note your uncertainty before proceeding.

### 2. Document Design Decisions as ADRs

Whenever you make or propose a significant architectural or design decision (choosing between libraries, defining a new interface, altering data flow), **you must create an ADR** to clearly document the decision rationale.

- **Create a short ADR markdown file (`docs/adr/00xx-short-description.md`):**

```markdown
# ADR 00XX: Short, Clear Decision Title

## Context & Problem

Briefly state the context and problem you’re solving. (1–3 sentences)

## Decision

Clearly state the decision made. (1–2 sentences)

## Alternatives Considered

Briefly list alternatives considered with pros/cons. (concise bullet points)

## Consequences

Clearly outline the positive/negative implications of this decision. (concise bullet points)
```

- **Include this ADR as part of your PR.**

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
## 📖 Summary of Documentation Changes

<!-- Briefly describe the updates and improvements you've made to the documentation -->

## ✏️ Changes

- Updated documentation for [module/component/...]
- Clarified usage examples
- Fixed typos, grammar, or formatting errors

## ✅ Testing & Verification

- [x] Reviewed changes locally
- [x] Verified links and references
- [ ] Requested review from relevant stakeholders (optional)
```

---

## ⚠️ Resolving Conflicts

Prompt instructions > nested AGENTS.md > this file.
