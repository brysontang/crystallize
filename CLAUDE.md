# Claude Code Guidelines for Crystallize

## Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/) with release-please for automated versioning.

### Version Bumps

| Prefix | Version Bump | When to Use |
|--------|--------------|-------------|
| `feat:` | **Minor** (0.X.0) | New user-facing features |
| `fix:` | **Patch** (0.0.X) | Bug fixes, DX improvements, small additions |
| `docs:` | None | Documentation only |
| `chore:` | None | Maintenance, deps, CI |
| `refactor:` | None | Code changes that don't add features or fix bugs |
| `test:` | None | Test additions/changes |

### Examples

```bash
# Minor bump (0.27.0 → 0.28.0) - significant new feature
feat: add experiment graphs for DAG workflows

# Patch bump (0.27.0 → 0.27.1) - DX improvements, small features
fix(dx): add experiment.debug() for quick iteration
fix: improve error messages for missing datasources

# No version bump - docs, maintenance
docs: update API reference
chore: update dependencies
refactor: simplify pipeline execution
```

### Scopes (Optional)

- `dx` - Developer experience improvements
- `cli` - CLI changes
- `core` - Core experiment/pipeline changes
- `plugins` - Plugin system changes

## Pull Requests

- Don't push or merge without explicit user request
- Run `pixi run -e dev lint` and `pixi run -e dev test` before committing
- Use the PR template format with Summary, Test plan sections

## Code Style

- Use `ruff` for linting (configured in pyproject.toml)
- Type hints required for public APIs
- Docstrings in NumPy format
