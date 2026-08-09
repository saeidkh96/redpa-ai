# ADR-0005: Incremental Clean Architecture Migration

Status: Accepted

## Context

RedPA already contains substantial working functionality.

## Decision

Do not perform a repository-wide folder rewrite only to achieve visual
architectural purity. Establish explicit dependency rules and migrate contexts
incrementally.

## Consequences

- lower regression risk;
- architecture improves without pausing feature development;
- legacy modules remain visible technical debt until migrated.
