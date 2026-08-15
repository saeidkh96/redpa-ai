# RedPA AI V10.0 — Governed Agent Runtime Architecture

## Purpose

V10 introduces a persistent governance layer around agent execution. The goal is not only to decide whether an action is allowed, but to preserve the full operational lifecycle: who initiated a run, what policy decided, whether human review blocked execution, how the run resumed, what side effect occurred, whether recovery was verified, and how the final result was evaluated.

## Runtime architecture

```text
                         +----------------------+
                         |   Next.js Control    |
                         |       Center         |
                         +----------+-----------+
                                    |
                                    v
+------------------+       +--------+---------+       +----------------------+
| Client / SDK /   | ----> | FastAPI Backend  | ----> | Governance V10       |
| CLI              |       | API + Services   |       | Run + Event Store    |
+------------------+       +--------+---------+       +----------+-----------+
                                    |                            |
                  +-----------------+------------------+         |
                  |                 |                  |         |
                  v                 v                  v         v
          +-------+------+  +-------+------+  +--------+----+ +--+-----------+
          | LangGraph /  |  | Ops Domain   |  | Policy      | | Evaluation   |
          | Agent Runtime|  | + Ops Agent  |  | Service     | | subsystem    |
          +-------+------+  +-------+------+  | Spring Boot | +--------------+
                  |                 |         +-------------+
          +-------+------+          |
          | MCP / A2A /  |          v
          | RAG / Memory |   Docker-controlled
          +--------------+   allowlisted recovery

Persistence / infrastructure:
PostgreSQL | Redis Streams | Qdrant | OpenTelemetry | Tempo | Prometheus | Grafana
```

## Governance lifecycle

A governed run is persisted before meaningful execution begins.

```text
CREATED -> RUNNING
              |
              +-> policy permits execution --------------------+
              |                                                |
              +-> policy requires review -> BLOCKED            |
                                             |                 |
                                      human approval            |
                                             |                 |
                                             +----> RUNNING <---+
                                                       |
                                                       v
                                                execution/result
                                                       |
                                    +------------------+------------------+
                                    |                                     |
                                    v                                     v
                                COMPLETED                               FAILED
                                    |
                                    v
                               EVALUATION
```

V10 Phase 3.1 makes the resume transition explicit: an approved and executable remediation resumes a blocked run to `RUNNING` before the side effect is attempted. A verified recovery can then finish the run as `COMPLETED`.

## Governance data model

The V10 persistence layer stores agent/governance runs and their event stream. A run carries identifiers for the user, agent, workflow and trace, lifecycle state, objective, input/output payloads, metadata, evaluation linkage, timestamps, and error state.

Events preserve stage-specific execution evidence such as:

- `run.created`
- `run.running`
- `policy.decision`
- `ops.diagnosis_started`
- `ops.diagnosis_completed`
- `ops.remediation_blocked`
- `ops.remediation_started`
- `ops.recovery_verified`
- `ops.governance_finalization_failed`
- `run.completed`
- `evaluation.completed`

## Policy boundary

The dedicated `policy-service` is a Spring Boot service in the primary Compose topology and is reachable internally at:

```text
http://policy-service:8090
```

Its health surface is:

```text
/actuator/health
```

The backend receives `POLICY_SERVICE_URL` explicitly and waits for the policy service health check before startup.

A policy result can distinguish the decision from executability. This allows a `REVIEW` decision to remain non-executable until human approval is supplied, while preserving the original risk and policy evidence in the trace.

## Governed operations integration

The V9 operations domain is retained as the operational API and is governed by V10.

```text
Incident
 -> governance run
 -> diagnosis
 -> policy decision
 -> optional BLOCKED state
 -> human approval
 -> resume
 -> allowlisted remediation
 -> recovery verification
 -> governance completion
 -> evaluation
```

The Ops Agent remains responsible for Docker-backed diagnosis and controlled restart execution. Governance is responsible for lifecycle correctness and evidence.

## Agent runtime integration

V10 governance hooks are integrated into the runtime paths used by planner, research, tool execution, Human Review, and chat/orchestration services. This keeps governance associated with the actual agent workflow instead of operating as a detached audit system.

## Observability

V10 keeps operational evidence across complementary layers:

- governance events for semantic execution history;
- OpenTelemetry for distributed traces;
- Tempo for trace storage;
- Prometheus for metrics;
- Grafana for dashboards;
- application logs for runtime diagnostics.

The main Compose stack starts OpenTelemetry Collector and Tempo with restart policies and makes the backend wait for collector startup.

## Release topology

Primary local services include:

- FastAPI backend — `8000`
- Next.js frontend — `3001`
- Grafana — `3000`
- Prometheus — `9090`
- RedPA Ops Agent — `8070`
- Policy Service — `8090`
- A2A Coordinator — `8050`
- Filesystem MCP — `8010`
- GitHub MCP — `8020`
- PostgreSQL MCP — `8030`
- Docker MCP — `8040`
- PostgreSQL — `5432`
- Redis — `6379`
- Qdrant — `6333/6334`
- OpenTelemetry Collector — `4317/4318`
- Tempo — `3200`

## Release verification

The V10 release candidate passed:

- V10 governance contract tests;
- runtime integration tests;
- Ops governance tests;
- Phase 3.1 lifecycle tests;
- release-hardening tests;
- full regression suite: **344 tests passed**;
- Docker Compose validation;
- frontend production build;
- backend, Ops Agent, and Policy Service health checks;
- end-to-end governed recovery ending in `COMPLETED` with evaluation score `1.0`.

## Design principle

V10 treats governance as runtime state, not only middleware. A production agent platform must be able to answer not just “was this action allowed?” but also “what happened before and after the decision, who approved it, did execution actually recover the system, and what evidence proves the run completed successfully?”
