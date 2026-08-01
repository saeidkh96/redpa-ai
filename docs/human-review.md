# Human-in-the-Loop Review

## Purpose

Human review provides an explicit control point when a workflow is sensitive, uncertain, or requires accountability.

## Lifecycle

```text
Pending
  ├── Approved → Resumed
  ├── Rejected → Closed
  └── Cancelled
```

## Reviewer Actions

A reviewer can:

- approve;
- reject;
- add feedback;
- resume an approved workflow.

## Safety Properties

The implementation should guarantee:

- ownership or reviewer authorization;
- only pending reviews can be decided;
- a second decision returns a conflict;
- timestamps and reviewer identity are stored;
- resume uses the approved decision;
- a review cannot be resumed twice.

## Stored Data

- user;
- conversation;
- message;
- reason;
- requested action;
- request content;
- action payload;
- reviewer;
- feedback;
- timestamps;
- resume metadata.
