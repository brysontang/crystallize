---
title: Viewing Provenance with Result.print_tree
description: Use Result.print_tree to inspect context changes and cache activity.
---

Crystallize records every context mutation during an experiment run. The
:class:`~crystallize.experiments.result.Result` object exposes a handy
:meth:`print_tree` method to visualize this provenance as a tree.

## Example

```python
result = experiment.run(treatments=[my_treatment], hypotheses=[my_hypothesis])
result.print_tree()  # shows treatments, replicates and steps
```

By default the tree groups by treatment, replicate and step. Pass a custom
format string to reorder the hierarchy or include ``"action"`` to display reads
and writes:

```python
result.print_tree("replicate > step > action")
```

When the optional ``rich`` package is installed, the output is colorized for
clarity. Otherwise a plain text tree is printed.

Use this method whenever you want a quick snapshot of what happened during a
run—it's especially useful for debugging cached pipeline steps.
