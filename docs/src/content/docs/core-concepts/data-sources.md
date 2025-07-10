---
title: Data Sources
description: Data sources in the Crystallize framework.
---

Explicitly introduce data sources as the foundational entry point of any Crystallize experiment, clearly stating that all data enters the framework through clearly defined data sources. Clearly articulate that data sources are intentionally unopinionated, explicitly flexible abstractions. Provide explicit examples: reading data clearly from CSV files, databases, synthetic data generators, APIs, and other common scenarios, clearly indicating the flexibility and power of this approach.

Explicitly describe how users define a custom datasource by extending the abstract `DataSource` class. Clearly indicate the expected implementation: users explicitly implement a simple `fetch()` method, explicitly returning the data. Reinforce explicitly why this minimalist design matters: data sources remain flexible yet explicitly clear, ensuring that experiments always have a clean, reliable, and reproducible starting point.
