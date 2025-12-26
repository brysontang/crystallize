# ADR 0005: LLM-Friendly XML Summaries

## Context & Problem

Users want to feed experiment outcomes into LLMs. The current CLI only surfaces human-oriented logs and summaries, which are brittle to parse programmatically and omit a structured view for downstream automation.

## Decision

Introduce an XML summary generator (`generate_xml_summary`) and surface it in the CLI run screen via an "LLM Data" tab so experiment results are always emitted in a machine-friendly, escaped format.

## Alternatives Considered

- Keep only the existing Rich/plain text summaries — easy to maintain but forces brittle scraping for LLM consumers.
- Emit JSON instead of XML — simpler for Python but harder to embed directly in prompt templates and lacks ordering/escaping guarantees users requested for XML.
- Provide an external script to transform results — decouples UI but adds extra setup and risks divergent output.

## Consequences

- Positive: Structured, deterministic XML is available immediately after runs for LLM pipelines; reduces the need for ad-hoc parsing; CLI UX gains a dedicated tab for copy/paste.
- Negative: We must keep XML output in sync with result schema changes and ensure escaping remains correct; adds minor UI real estate and maintenance overhead.
