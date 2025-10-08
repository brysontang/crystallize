# Crystallize Documentation Site

This directory contains the Starlight (Astro) project that powers the Crystallize documentation portal.

## Project Layout

```
docs/
├── astro.config.mjs        # Starlight configuration and sidebar definition
├── package.json            # Node dependencies (Astro, Starlight, theme plugins)
├── src/
│   ├── assets/             # Static assets referenced from documentation pages
│   └── content/            # Markdown/MDX sources organised by Diátaxis domains
│       └── docs/
│           ├── tutorials/   # Step-by-step walkthroughs
│           ├── how-to/      # Task-oriented recipes
│           ├── explanation/ # Conceptual deep dives
│           └── reference/   # Auto-generated API reference (see `generate_docs.py`)
└── adr/                    # Architectural decision records
```

## Local Development

```bash
cd docs
npm install          # Installs Astro, Starlight, and theme plugins
npm run dev          # Launches the documentation site at http://localhost:4321
```

The dev server supports hot reloading; save Markdown files to preview updates instantly.

## Building for Production

```bash
npm run build        # Outputs the static site to docs/dist
```

Deploy the generated `dist/` directory to GitHub Pages or any static host. The repository’s GitHub Pages workflow uses the same build command.

## Regenerating API Reference

The pages under `src/content/docs/reference/` are generated via Lazydocs. After changing the Python APIs:

```bash
python3.10 generate_docs.py
```

This script walks the `crystallize/` package and refreshes each Markdown file with the latest signatures and docstrings.

## Writing Guidelines

- Follow the Diátaxis classification already reflected in the folder structure.
- Prefer short, task-focused sections. Link to examples under `/examples` whenever possible rather than copying long code listings.
- Keep tutorial code aligned with `examples/` to ensure it stays runnable.
- For significant architectural choices, add a new ADR under `docs/adr/` following the template in `AGENTS.md`.
