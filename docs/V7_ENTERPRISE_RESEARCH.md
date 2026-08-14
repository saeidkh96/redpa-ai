# RedPA AI V7.0 — Enterprise Research Workspace

## Purpose

V7 adds a real end-to-end application workflow to RedPA: evidence-first enterprise research with persisted execution state and a live operator view.

## Flow

```text
Research Question
  -> queued persisted run
  -> planning
  -> web research via existing Research Agent / DDGS
  -> evidence ranking
  -> deterministic quality evaluation
  -> evidence-first Markdown report
  -> completed persisted run
```

The Control Plane polls persisted state so an operator can watch stage and progress changes without inventing a separate client-side execution model.

## API

```text
POST /api/v1/research/runs
GET  /api/v1/research/runs
GET  /api/v1/research/runs/{run_id}
```

Example request:

```json
{
  "query": "Compare enterprise AI agent platforms",
  "max_results": 8,
  "minimum_quality_score": 0.65
}
```

## Persistence

Alembic migration `v70a1b2c3d4e` adds:

- `enterprise_research_runs`
- `enterprise_research_events`

The run stores status, current stage, progress, provider, ranked evidence, quality result, report, error and timestamps. Timeline events record stage transitions and execution metadata.

## Quality

The V7 quality score is deterministic rather than LLM-judged:

```text
quality = coverage * 0.60 + source_diversity * 0.40
```

Coverage measures collected evidence against the configured target. Source diversity measures the ratio of unique source domains to evidence items.

A result below `minimum_quality_score` still completes, but its report is marked `REVIEW` rather than `PASS`.

## Provenance

Reports preserve:

- source title;
- source domain;
- source URL;
- retrieved snippet;
- retrieval score.

V7 does not claim that the generated report independently verifies facts outside the retrieved evidence context.

## Control Plane

```text
http://localhost:3001/control-plane/research
```

The page provides:

- start form;
- persisted run history;
- live progress and execution stage;
- timeline events;
- evidence cards;
- quality metrics;
- final report.

## SDK / CLI

```bash
redpa research start --query "..."
redpa research list
redpa research get <uuid>
```

The synchronous and asynchronous Python clients expose matching create/list/detail operations.

## Runtime dependency

The workspace uses the existing `ResearchAgentService`, which currently performs web retrieval with DDGS. Internet connectivity is therefore required for a successful real research execution.

## V7 boundaries

V7 intentionally does not claim:

- autonomous factual verification beyond retrieved source evidence;
- browser automation;
- a live hosted production deployment;
- recovery of an in-flight background task after process termination.

Those remain separate reliability/product concerns.
