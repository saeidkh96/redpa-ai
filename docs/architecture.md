# RedPA AI v19.0.0 Architecture

This document describes the architecture represented by the **v18.1.0**
repository snapshot. RedPA AI is a production-oriented Agentic AI
platform built around explicit execution, governance, reliability,
integration, and audit boundaries.

The architecture separates **reasoning** from **permission**, **agent
delegation** from **tool execution**, and **runtime capability** from
**release-readiness evidence**.

## Architecture Scope --- v19.0.0

RedPA AI v19 is a production-oriented, governed Agentic AI platform
composed of a FastAPI platform API, Next.js Control Plane, stateful
agent runtime, MCP and A2A interoperability, model-provider abstraction,
Human-in-the-Loop and policy gates, durable execution, operational
recovery, persistent run history, enterprise analytics, event
processing, observability, and multi-cloud infrastructure foundations.

The architecture intentionally distinguishes **implemented/validated
runtime behavior** from **integration or deployment readiness**:

-   Docker Compose is the strongest validated integration target.
-   Microsoft V18.4 is contract/readiness based, not a live tenant
    integration.
-   AWS V19 is Pulumi preview validated, not deployed with `pulumi up`.
-   Kubernetes/Helm and Azure/Pulumi are deployment/reference paths
    unless separately validated in an environment.

## 1. System Context

``` mermaid
flowchart LR
    User[Operator / Developer]
    CP[Next.js Control Plane]
    SDK[Python SDK / CLI]
    API[FastAPI Platform API]
    External[External Models / Services]
    Infra[Managed / Local Infrastructure]

    User --> CP
    User --> SDK
    CP --> API
    SDK --> API
    API --> External
    API --> Infra
```

The FastAPI backend is the primary platform boundary. The Control Plane,
SDK, CLI, background services, agents, MCP services, and policy service
compose around that API and the shared persistence/event infrastructure.

## 2. Container / Runtime View

``` mermaid
flowchart TB
    Client[Control Plane / SDK / CLI]

    subgraph APIPlane[API & Governance Plane]
        API[FastAPI Backend :8000]
        Policy[Spring Boot Policy Service :8090]
        Ops[Ops Agent]
        Worker[Background Worker]
        Scheduler[Background Scheduler]
        Outbox[Outbox Publisher]
    end

    subgraph AgentPlane[A2A Agent Plane]
        Coord[A2A Coordinator :8050]
        Research[Research Agent :8061]
        PGAgent[PostgreSQL Agent :8062]
        DockerAgent[Docker Agent :8063]
        FSAgent[Filesystem Agent :8064]
        GHAgent[GitHub Agent :8065]
    end

    subgraph ToolPlane[MCP Tool Plane]
        FSMCP[Filesystem MCP :8010]
        GHMCP[GitHub MCP :8020]
        PGMCP[PostgreSQL MCP :8030]
        DockerMCP[Docker MCP :8040]
    end

    subgraph Data[Persistence & Coordination]
        PG[(PostgreSQL 17)]
        Q[(Qdrant)]
        Redis[(Redis / Streams)]
    end

    subgraph Observe[Observability]
        Prom[Prometheus]
        Grafana[Grafana]
        OTEL[OpenTelemetry Collector]
        Tempo[Tempo]
    end

    Client --> API
    API --> Policy
    API --> Ops
    API --> Coord
    Coord --> Research
    Coord --> PGAgent
    Coord --> DockerAgent
    Coord --> FSAgent
    Coord --> GHAgent

    API --> FSMCP
    API --> GHMCP
    API --> PGMCP
    API --> DockerMCP

    API --> PG
    API --> Q
    API --> Redis
    Worker --> PG
    Scheduler --> PG
    Outbox --> Redis

    API --> Prom
    API --> OTEL
    OTEL --> Tempo
    Prom --> Grafana
```

### Runtime responsibilities

  -----------------------------------------------------------------------
  Component                           Responsibility
  ----------------------------------- -----------------------------------
  FastAPI backend                     API surface, orchestration,
                                      governance integration, platform
                                      services

  Next.js Control Plane               operator-facing platform views and
                                      controls

  Spring Boot Policy Service          externalized ALLOW/REVIEW/DENY
                                      policy boundary

  Ops Agent                           operational diagnosis/remediation
                                      path

  A2A Coordinator                     specialist-agent
                                      discovery/delegation boundary

  MCP services                        structured tool interoperability
                                      boundary

  Background Worker/Scheduler         asynchronous and scheduled platform
                                      work

  Outbox Publisher                    event publication from
                                      transactional state

  PostgreSQL                          durable relational/runtime/audit
                                      state

  Qdrant                              vector retrieval and semantic
                                      memory

  Redis                               coordination, caching and event
                                      streams

  Prometheus/Grafana                  metrics and dashboards

  OpenTelemetry/Tempo                 distributed tracing path
  -----------------------------------------------------------------------

## 3. Core Agentic Runtime

The platform's agent runtime composes planner/router behavior,
research/RAG, specialist agents, MCP tools, A2A delegation, durable
workflows, memory, and evaluation.

``` mermaid
flowchart LR
    Request[Request]
    Router[Planner / Router]
    Research[Research / RAG]
    A2A[A2A Delegation]
    MCP[MCP Tool Execution]
    Review[Human Review]
    Result[Result]

    Request --> Router
    Router --> Research
    Router --> A2A
    Router --> MCP
    Router --> Review
    Research --> Result
    A2A --> Result
    MCP --> Result
    Review --> Result
```

MCP and A2A are intentionally distinct:

-   **MCP** is the tool boundary: discovery, structured arguments and
    controlled execution of filesystem, GitHub, PostgreSQL and Docker
    capabilities.
-   **A2A** is the agent boundary: capability discovery, specialist
    selection, delegation, parallel/distributed work and result
    aggregation.

## 4. Governed Execution Boundary

V10 establishes governance as runtime state rather than a detached
pre-request check.

``` mermaid
stateDiagram-v2
    [*] --> CREATED
    CREATED --> RUNNING
    RUNNING --> RUNNING: policy ALLOW
    RUNNING --> BLOCKED: policy REVIEW
    BLOCKED --> RUNNING: explicit approval / resume
    BLOCKED --> FAILED: rejection / invalid continuation
    RUNNING --> FAILED: policy DENY / execution failure
    RUNNING --> COMPLETED: execution + verification succeeds
    COMPLETED --> [*]
    FAILED --> [*]
```

The important architectural rule is that autonomous reasoning does not
grant autonomous permission. Potentially destructive or high-risk
operations remain behind policy and/or explicit Human-in-the-Loop
approval.

## 5. Production Operations and Recovery

The operations path composes detection, diagnosis, policy, approval,
remediation, and verification.

``` mermaid
flowchart LR
    Detect[Detect Incident]
    Persist[Persist Incident]
    Diagnose[Ops Agent Diagnosis]
    Action[Remediation Proposal]
    Policy[Policy Decision]
    HITL[Human Approval]
    Execute[Controlled Execution]
    Verify[Recovery Verification]
    Close[Recovered / Closed]
    Fail[Fail Closed]

    Detect --> Persist --> Diagnose --> Action --> Policy
    Policy -->|ALLOW| Execute
    Policy -->|REVIEW| HITL
    HITL -->|Approved| Execute
    HITL -->|Rejected| Fail
    Policy -->|DENY| Fail
    Execute --> Verify
    Verify -->|Pass| Close
    Verify -->|Fail| Fail
```

Recovery is considered successful only after verification. A failed
verification does not silently convert into success.

## 6. V12 Self-Healing Multi-Agent Runtime

V12 extends operational reliability into agent routing and failover.

``` text
agent failure
-> failure record
-> capability discovery
-> health-aware replacement
-> policy / optional approval
-> context handoff
-> replacement execution
-> verification
-> persisted checkpoint
-> recovery
-> controlled rejoin
```

Key invariants implemented by the V12 layer:

-   the failed agent cannot be selected as its own replacement;
-   high-risk failover remains approval-aware;
-   replacement execution is verification-gated;
-   duplicate failover execution is idempotent;
-   checkpoint state persists across backend restart;
-   rejoin requires a healthy state and cleared failure streak.

## 7. V13 Adaptive Governance

V13 turns runtime governance signals into auditable recommendations
while preserving an explicit application boundary.

``` mermaid
flowchart LR
    Signals[Runtime Signals]
    History[Historical Aggregation]
    Recommend[Recommendation]
    Risk[Risk / Confidence]
    Proposal[Versioned Proposal]
    Review[Human Review]
    Shadow[Shadow Evaluation]
    Apply[Explicit Apply]
    Rollback[Rollback]

    Signals --> History --> Recommend --> Risk --> Proposal
    Proposal --> Review --> Shadow --> Apply
    Apply --> Rollback
```

Adaptive governance may recommend policy changes; it does **not**
silently auto-apply them.

## 8. V14 Security & Compliance Evidence

V14 provides an evidence-oriented compliance lifecycle:

``` text
versioned control
-> evidence collection
-> completeness
-> SHA-256 integrity
-> freshness / expiry
-> risk assessment
-> approval boundary
-> persisted audit record
-> export
-> validation gate
```

The data model separates compliance controls, collected evidence, and
assessment records. Evidence metadata is persisted separately from
SQLAlchemy's declarative `metadata` attribute while retaining the
database column name `metadata`.

## 9. V15 Cloud Readiness

V15 models cloud-readiness as an explicit assessment/gate rather than
assuming readiness from the presence of infrastructure files.

Assessment areas include inventory, health dependencies, backup/restore,
secrets/IAM, capacity, observability, resilience, risk scoring,
deployment gate, and validation gate.

The repository also contains Kubernetes/Helm and Azure/Pulumi assets.
These are deployment/reference assets; their presence does not establish
a live production deployment.

## 10. V16 Continuous Evaluation

V16 introduces a controlled model/agent change path:

``` text
dataset
-> baseline
-> candidate
-> quality evaluation
-> safety evaluation
-> regression analysis
-> shadow evaluation
-> rollout decision
-> rollback capability
-> validation gate
```

A candidate is not promoted solely because it exists or scores higher on
one metric. Rollout is a governed decision with regression/safety
boundaries.

## 11. V17 Enterprise Integration Hub

V17 treats integrations as governed capabilities rather than
unrestricted outbound access.

``` text
connector registry
-> auth scope
-> secret handling
-> network boundary
-> write boundary
-> audit
-> rate limit
-> risk assessment
-> approval gate
-> validation gate
```

Write access, external-network access, secret handling and approval
requirements contribute to connector risk and runtime restrictions.

## 12. V18 Trusted Agent Registry

V18 adds a trust boundary before agents become routable platform
participants.

``` text
identity
-> signed manifest
-> provenance
-> declared capabilities
-> health
-> governance compatibility
-> policy profile
-> trust score/state
-> routing boundary
-> validation gate
```

Trust is not equivalent to simple registration. Agent identity, health
and governance compatibility influence whether the agent can participate
in routing.

## 13. V18.1 Production Hardening

V18.1 is a release-validation layer over V12--V18 rather than another
autonomous capability.

``` mermaid
flowchart LR
    Integration[V12-V18 Integration]
    Migration[Migration Chain]
    APIE2E[Authenticated API E2E]
    Restart[Persistence / Restart]
    Failure[Failure Injection]
    Security[Security Boundaries]
    Docker[Docker Runtime]
    Obs[Observability]
    Evidence[Release Evidence]
    Gate[Regression Gate]

    Integration --> Migration --> APIE2E --> Restart --> Failure
    Failure --> Security --> Docker --> Obs --> Evidence --> Gate
```

The machine-readable report for the validated repository snapshot
records all ten stages as PASS and identifies the V18.1 migration head
as `v270a1b2c3d4e`.

## 14. V18.2 Production E2E Demonstration

V18.2 validates the major production-oriented runtime boundaries
together in a controlled end-to-end execution rather than treating them
as isolated features.

``` text
Runtime discovery
  -> primary-agent routing
  -> trusted-agent boundary
  -> governance boundary
  -> controlled failure injection
  -> self-healing fallback
  -> real A2A fallback execution
  -> recovery and workflow rejoin
  -> continuous evaluation
  -> machine-readable audit evidence
```

The demonstrated recovery path resolves the primary agent, injects a
controlled failure before delegation, selects a connected fallback
agent, executes through the shipped A2A runtime, rejoins the workflow,
evaluates the recovered result, and persists release evidence.

This is validation of the shipped runtime path; it does not imply
unrestricted autonomous side effects.

## 15. V18.3 Persistent Run History & Control Plane

V18.3 adds a persistent execution-history boundary backed by PostgreSQL.

``` mermaid
flowchart LR
    Runtime[Governed / Agent Runtime]
    History[Run History Repository]
    DB[(PostgreSQL)]
    API[Run History API]
    UI[Control Plane Run History]

    Runtime --> History
    History --> DB
    DB --> API
    API --> UI
```

Persisted evidence includes:

-   execution/run records;
-   trace identifiers;
-   primary and fallback agent information;
-   fallback and recovery evidence;
-   execution latency;
-   evaluation scores;
-   summary aggregation for Control Plane visibility.

The history layer turns transient agent execution into queryable
operational evidence and is also the source for V18.5 analytics.

## 16. V18.4 Microsoft Enterprise Integration Readiness

V18.4 defines credential-free enterprise integration contracts for
Microsoft Power Platform scenarios.

``` mermaid
flowchart LR
    RedPA[RedPA Governed Runtime]
    Contract[Microsoft Integration Contract]
    PA[Power Automate]
    Human[Human Approval]
    Action[Governed RedPA Action]
    Audit[(Audit Evidence)]

    RedPA --> Contract
    Contract --> PA
    PA --> Human
    Human --> Action
    Action --> Audit
```

Supported contract/readiness surfaces include:

-   Power Automate approval flows;
-   explicit `requires_approval=true` semantics;
-   Copilot Studio REST action contracts;
-   platform summary;
-   agent status;
-   incident summary;
-   Microsoft 365-oriented integration scenarios.

**Boundary:** the repository provides integration contracts and
readiness. It does not claim a live Power Automate, Copilot Studio,
Teams, Outlook, Microsoft 365, or tenant connection. Production
credentials remain external secrets.

## 17. V18.5 Enterprise Analytics

V18.5 exposes operational analytics from persisted V18.3 run history.

``` mermaid
flowchart LR
    History[(V18.3 Run History)]
    Analytics[Enterprise Analytics API]
    KPI[Operational KPI Summary]
    JSON[Power BI-friendly JSON]
    CSV[Excel-compatible CSV]
    Tableau[Tableau / Other BI Consumers]

    History --> Analytics
    Analytics --> KPI
    Analytics --> JSON
    Analytics --> CSV
    JSON --> Tableau
    CSV --> Tableau
```

The analytics boundary includes total runs, success/fallback/recovery
evidence, latency, evaluation scores, policy-denial visibility, and
agent reliability signals where supported by persisted records.

Power BI and Excel are data-consumer targets; RedPA does not embed a
second BI frontend inside the platform.

## 18. V19 Multi-Cloud Deployment Foundation

V19 keeps the existing Azure Pulumi path and adds an AWS Pulumi
foundation.

``` mermaid
flowchart TB
    Repo[RedPA Repository]

    subgraph Local[Validated Local Integration]
        Compose[Docker Compose]
        Runtime[RedPA Runtime]
        Compose --> Runtime
    end

    subgraph Azure[Azure Foundation]
        AzurePulumi[Pulumi]
        AzureAssets[Azure Infrastructure Assets]
        AzurePulumi --> AzureAssets
    end

    subgraph AWS[AWS V19 Foundation]
        AWSPulumi[Pulumi]
        VPC[VPC]
        ECS[ECS Cluster]
        ECR[ECR Repository]
        CW[CloudWatch Log Group]

        AWSPulumi --> VPC
        AWSPulumi --> ECS
        AWSPulumi --> ECR
        AWSPulumi --> CW
    end

    subgraph K8s[Kubernetes Path]
        Helm[Helm Chart]
        Kube[Kubernetes]
        Helm --> Kube
    end

    Repo --> Compose
    Repo --> AzurePulumi
    Repo --> AWSPulumi
    Repo --> Helm
```

The AWS foundation currently defines infrastructure in `eu-central-1`
for:

-   VPC;
-   ECS cluster;
-   ECR repository;
-   CloudWatch log group;
-   Pulumi project and stack configuration.

`pulumi preview` is validated. **`pulumi up` has not been run and no AWS
resources are claimed as deployed.** Azure/Pulumi and Kubernetes/Helm
remain deployment/reference paths unless separately validated in a real
environment.

## 19. Persistence Model

PostgreSQL is the durable system of record for relational platform
state, including governed runtime state, incidents, evolution records,
self-healing checkpoints, adaptive-governance data, compliance data, and
production-hardening evidence.

Qdrant is used for vector retrieval/semantic memory. Redis supports
runtime coordination, caching, and stream-based event publication.

A central architectural principle is that important governance/recovery
state should survive process restart rather than live only in memory.

## 20. Event and Background Processing

The repository includes:

-   transactional outbox/event APIs;
-   an Outbox Publisher;
-   background worker and scheduler services;
-   Redis-backed coordination and Redis Streams publication.

This separates synchronous request handling from asynchronous platform
work and provides a path for auditable event-driven processing.

## 21. Observability

The local integration stack includes:

``` text
application metrics -> Prometheus -> Grafana
application traces  -> OpenTelemetry Collector -> Tempo
application events/logs -> structured/correlated runtime evidence
```

Observability is part of the V18.1 hardening gate; the architecture does
not treat telemetry as an optional diagram-only component.

## 22. Security and Governance Boundaries

The main control boundaries are:

1.  **Authentication and tenancy/RBAC foundations** at the API/platform
    layer.
2.  **Policy enforcement** for governed operations.
3.  **Human Review** for actions requiring explicit approval.
4.  **MCP execution controls** around tool invocation.
5.  **Connector governance** around secrets, networks and write access.
6.  **Trusted-agent routing** around identity, provenance, health and
    governance compatibility.
7.  **Fail-closed recovery** when execution or verification cannot
    establish a safe result.
8.  **Persisted audit/evidence** for governance and release decisions.

## 23. Deployment View

### Validated local integration target

The primary integrated runtime is `docker-compose.yml`, containing the
backend, frontend, data services, policy service, agents, MCP services,
background processes and observability components.

### Kubernetes / Helm

The repository contains Kubernetes networking/namespace assets and a
Helm chart. These represent a deployment path and packaging boundary;
they should not be interpreted as proof of a currently running
production cluster.

### Azure / Pulumi

`infra/azure/` contains Pulumi-based Azure infrastructure modules and
production-oriented runbook/configuration assets. This is
infrastructure-as-code/reference architecture until validated against an
actual target subscription/environment.

## 24. API Architecture

The API is versioned under `/api/v1`. Important runtime/evolution
boundaries include:

``` text
/api/v1/governance/v10
/api/v1/operations/v9
/api/v1/platform/evolution
/api/v1/adaptive-governance/v13
/api/v1/security-compliance/v14
/api/v1/cloud-readiness/v15
/api/v1/continuous-evaluation/v16
/api/v1/enterprise-integration/v17
/api/v1/trusted-agents/v18
/api/v1/production-hardening/v18.1
```

Additional routers cover authentication, users, conversations/messages,
chat/LLM, documents/RAG, Human Review, MCP, tools, agents, memory,
evaluations, guardrails, policy enforcement, tenants, OAuth, events,
analytics, connectors, model gateway, monitoring and platform health.

## 25. Release Validation Boundary

For v18.1.0, the repository records:

``` text
Full regression suite: 418 passed
Alembic head:          v270a1b2c3d4e
Hardening stages:      10 / 10 PASS
Overall status:        PASS
```

The report is evidence-oriented. It demonstrates the repository's
validation gates and tested local integration behavior; it does not by
itself claim an external production deployment, production traffic, or
an SLA.

## 26. Architectural Principles

-   Autonomous reasoning and autonomous permission are separate
    concerns.
-   High-risk side effects require explicit governance boundaries.
-   Durable state is preferred for workflow, governance and recovery
    checkpoints.
-   Failure handling must be idempotent and restart-safe.
-   Recovery requires verification.
-   Adaptive policy changes are recommendation-first and explicit-apply.
-   External connectors and remote agents are trust boundaries.
-   Evaluation precedes rollout.
-   Observability and release evidence are part of the runtime quality
    model.
-   Deployment readiness is validated through evidence rather than
    inferred from repository structure.

## 27. Related Architecture Documentation

The repository also contains deeper architecture views and historical
design material:

-   `docs/architecture/c4.md`
-   `docs/architecture/arc42.md`
-   `docs/architecture/ddd.md`
-   `docs/architecture/adr/`
-   `docs/MCP_PLATFORM.md`
-   `docs/A2A_PLATFORM.md`
-   `docs/TOOL_RUNTIME.md`
-   `docs/HUMAN_REVIEW.md`
-   `docs/V10_GOVERNED_AGENT_RUNTIME.md`
-   `docs/V12_SELF_HEALING_STAGE1_10.md`
-   `docs/V13_ADAPTIVE_GOVERNANCE_STAGE1_10.md`
-   `docs/V14_SECURITY_COMPLIANCE_STAGE1_10.md`
-   `docs/V15_PRODUCTION_CLOUD_PLATFORM_STAGE1_10.md`
-   `docs/V16_AGENT_EVALUATION_AND_CONTINUOUS_IMPROVEMENT_STAGE1_10.md`
-   `docs/V17_ENTERPRISE_INTEGRATION_HUB_STAGE1_10.md`
-   `docs/V18_TRUSTED_AGENT_REGISTRY_STAGE1_10.md`
-   `docs/V18_1_PRODUCTION_HARDENING_STAGE1_10.md`
