# ADR-0003: Provider-Neutral Model Gateway

Status: Accepted

## Decision

Agents depend on the Model Gateway abstraction rather than specific model
providers.

## Consequences

Provider selection, fallback, timeout, retry, and circuit breaking are
centralized and model providers remain replaceable.
