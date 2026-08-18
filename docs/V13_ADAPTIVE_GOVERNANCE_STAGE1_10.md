# RedPA AI V13 — Adaptive Governance Stage 1–10

## Goal

Turn the existing V13 policy-recommendation milestone into an evidence-driven,
versioned, auditable governance lifecycle while preserving the RedPA rule:

**adaptive governance may recommend changes, but it must never silently auto-apply them.**

## Stages

1. Persist runtime governance signals.
2. Aggregate historical evidence by action/agent/tenant.
3. Produce evidence-driven policy recommendations.
4. Compute decision/risk/confidence.
5. Require explicit human review for high-risk recommendations.
6. Persist versioned policy proposals.
7. Shadow-evaluate proposed policy changes before application.
8. Apply only explicitly approved + shadow-safe proposals.
9. Roll back applied proposals with evidence.
10. Generate a machine-readable V13 PASS/FAIL validation report.

## Target lifecycle

```text
runtime signals
-> historical evidence
-> recommendation
-> risk/confidence
-> versioned proposal
-> human review
-> shadow evaluation
-> explicit apply
-> audit evidence
-> optional rollback
```

`auto_applied` remains false by design.
