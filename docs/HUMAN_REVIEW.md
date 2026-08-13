# Human Review

## Purpose

Human Review prevents sensitive actions from executing without explicit approval.

RedPA currently contains two approval boundaries:

1. persisted Human Review for normal LangGraph workflows;
2. an A2A Multi-Agent approval gate that stops sensitive distributed workflows before remote delegation.

## Persisted Workflow Lifecycle

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
- timestamps;
- resume metadata.

## Resume

Approved reviews can resume the workflow without creating a duplicate review.

The resumed state records that approval has already been granted.

## A2A Approval Gate

The Multi-Agent API evaluates the original request before creating or dispatching subtasks.

Current high-risk categories include:

- sending email;
- deleting or removing data;
- restarting or stopping infrastructure;
- modifying files, records, or databases;
- processing refunds;
- production deployment.

Example request:

```json
{
  "request": "Send an email to the project manager",
  "subtasks": [],
  "max_parallelism": 2,
  "timeout_seconds": 90,
  "approval_granted": false
}
```

Expected result:

```text
success: false
approval_required: true
results: []
```

No Remote Agent is contacted before approval.

## Current Boundary

The A2A approval gate currently uses the `approval_granted` request field.

It is not yet persisted as a Human Review database record. Integrating this gate with the existing persisted review queue is planned for the durable-workflow phase.

## Future Work

- persisted A2A approval records;
- reviewer roles;
- approval expiration;
- multi-reviewer quorum;
- signed approval evidence;
- audit exports;
- resume tokens for distributed workflows.
