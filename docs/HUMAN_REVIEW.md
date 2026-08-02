# Human Review

## Purpose

Human Review prevents sensitive actions from executing without explicit approval.

## Lifecycle

```text
Planner identifies sensitive action
  → review record created
  → workflow pauses
  → reviewer approves or rejects
  → workflow resumes or terminates
```

## Persisted Data

A review may contain:

- status;
- reason;
- requested action;
- payload;
- conversation reference;
- decision metadata;
- timestamps.

## Resume

Approved reviews can resume the workflow without creating a duplicate review. The resumed state records that approval has already been granted.

## Future Work

- reviewer roles;
- approval policies;
- expiration;
- multi-reviewer quorum;
- audit exports;
- A2A approval boundaries.
