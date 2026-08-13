# ADR-0004: Policy Before External Side Effects

Status: Accepted

## Decision

External or risky tool actions must pass policy enforcement before execution.

ALLOW proceeds, REVIEW creates or requires human approval, and DENY blocks
execution.

## Consequences

Safety decisions are auditable and consistent across tool boundaries.
