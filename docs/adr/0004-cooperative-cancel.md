# ADR 0004: Cooperative cancellation for RunScreen experiments

## Context & Problem

The RunScreen used `asyncio.run` to execute experiments, preventing the Cancel button from stopping the running coroutine. This often left runs lingering and made the UI unresponsive.

## Decision

Create an explicit event loop and task in the worker thread so the Cancel button can request `task.cancel()` via `loop.call_soon_threadsafe`, allowing cooperative cancellation.

## Alternatives Considered

- Keep using `asyncio.run` (simple but impossible to cancel once started).
- Forcefully terminate the worker thread (unsafe; risks resource leaks).

## Consequences

- Cancellation propagates quickly and cleanly.
- Slightly more complex worker setup.
- If cancellation stalls, the UI warns and offers an unsafe force stop.

