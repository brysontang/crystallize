# Claude Code Guidelines for Crystallize

## Project Overview

Crystallize v1 is a minimal experiment framework. The entire API is one function: `run()`.

## Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/) with release-please.

| Prefix | Version Bump | When to Use |
|--------|--------------|-------------|
| `feat:` | **Minor** (1.X.0) | New features |
| `feat!:` | **Major** (X.0.0) | Breaking changes |
| `fix:` | **Patch** (1.0.X) | Bug fixes, improvements |
| `docs:` | None | Documentation |
| `chore:` | None | Maintenance |

## Development

```bash
# Run tests
pixi run -e dev test

# Run linter
pixi run -e dev lint

# Format code
pixi run -e dev format
```

## Code Style

- Use `ruff` for linting
- Type hints for public APIs
- Keep it simple - the whole package is ~400 lines
