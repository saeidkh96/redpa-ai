# RedPA AI v20.0.0 Architecture

RedPA AI is a production-oriented, governed Agentic AI platform built around explicit execution, governance, reliability, recovery, interoperability, audit, evaluation, and infrastructure boundaries.

The central architectural rule is:

> **Reasoning != Permission**

An agent may reason, retrieve, delegate, diagnose, evaluate, and recommend an action without automatically being authorized to perform a destructive or high-risk side effect.

## Architecture Scope — v20.0.0

RedPA AI v20.0.0 combines:

- FastAPI platform APIs
- Next.js Control Plane
- LangGraph workflows
- planner/router behavior
- RAG and semantic retrieval
- Qdrant
- PostgreSQL
- Redis
- MCP tool services
- A2A agent delegation
- Human-in-the-Loop controls
- governed execution
- policy boundaries
- trusted-agent routing
- self-healing workflows
- continuous evaluation
- persistent run history
- enterprise analytics
- event/background processing
- Prometheus / Grafana
- OpenTelemetry / Tempo
- AWS ECS/Fargate
- AWS Application Load Balancer
- Amazon RDS PostgreSQL
- AWS Secrets Manager
- Amazon SNS
- AWS Application Auto Scaling
- CloudWatch
- ECS Container Insights
- Pulumi IaC
- Docker Compose
- Kubernetes/Helm deployment assets
- Azure/Pulumi infrastructure assets

The architecture distinguishes:

- implemented runtime behavior
- validated deployment behavior
- integration readiness
- infrastructure/reference assets
- production claims that are intentionally not made

## 1. System Context

```mermaid
flowchart LR
    User["Operator / Developer"]
    CP["Next.js Control Plane"]
    SDK["Python SDK / CLI"]
    REST["REST Clients"]
    ALB["AWS Application Load Balancer"]
    API["FastAPI Platform API"]
    External["External Models / Services"]
    Infra["Managed / Local Infrastructure"]

    User --> CP
    User --> SDK
    CP --> ALB
    SDK --> ALB
    REST --> ALB
    ALB --> API
    API --> External
    API --> Infra
```

The FastAPI backend is the central application boundary. The Control Plane, SDK, CLI, background services, agent runtime, MCP services, A2A agents, policy service, data stores, and observability systems compose around this API and its governed execution model.

## 2. Architectural Planes

RedPA separates responsibilities into explicit planes.

### 2.1 Client / Access Plane

- Next.js Control Plane
- REST API clients
- Python SDK
- CLI
- external systems

### 2.2 AWS Ingress Plane

- Application Load Balancer
- public HTTP entry point
- target group
- ALB security group
- controlled ALB-to-backend security-group path

### 2.3 API Plane

- FastAPI backend
- authentication
- tenancy/RBAC foundations
- health and liveness
- API routing
- audit/evidence
- Control Plane APIs

### 2.4 Governed Agent Runtime

- planner/router
- LangGraph workflows
- durable execution
- Human-in-the-Loop
- policy decisions
- approval-aware resume
- trusted-agent routing
- evaluation
- recovery

### 2.5 Agent Communication Plane

- A2A coordinator
- specialist agents
- MCP services
- delegated execution
- structured tool execution

### 2.6 Retrieval / Memory Plane

- RAG
- Qdrant
- semantic memory
- PostgreSQL-backed state

### 2.7 Model Gateway

- provider abstraction
- model routing
- provider adapters
- model status/economics boundaries

### 2.8 Governance / HITL Plane

- policy enforcement
- ALLOW / REVIEW / DENY
- explicit approval
- rejection
- resume
- audit

### 2.9 Operations / Self-Healing Plane

- incident persistence
- diagnosis
- remediation proposals
- controlled execution
- verification
- task/agent recovery
- checkpoint persistence
- controlled rejoin

### 2.10 Data Plane

- PostgreSQL / Amazon RDS
- Redis / Streams
- Qdrant
- run history
- audit/evidence state

### 2.11 Observability Plane

- application metrics
- Prometheus
- Grafana
- OpenTelemetry
- Tempo
- CloudWatch Logs
- CloudWatch Alarms
- ECS Container Insights

### 2.12 Infrastructure / Deployment Plane

- Docker Compose
- Pulumi AWS
- Pulumi Azure
- Kubernetes / Helm

## 3. Container / Runtime View

```mermaid
flowchart TB
    Client["Control Plane / SDK / CLI"]

    subgraph Ingress["Ingress"]
        ALB["AWS ALB"]
    end

    subgraph APIPlane["API & Governance Plane"]
        API["FastAPI Backend :8000"]
        Policy["Spring Boot Policy Service :8090"]
        Ops["Ops Agent"]
        Worker["Background Worker"]
        Scheduler["Background Scheduler"]
        Outbox["Outbox Publisher"]
    end

    subgraph AgentPlane["A2A Agent Plane"]
        Coord["A2A Coordinator :8050"]
        Research["Research Agent :8061"]
        PGAgent["PostgreSQL Agent :8062"]
        DockerAgent["Docker Agent :8063"]
        FSAgent["Filesystem Agent :8064"]
        GHAgent["GitHub Agent :8065"]
    end

    subgraph ToolPlane["MCP Tool Plane"]
        FSMCP["Filesystem MCP :8010"]
        GHMCP["GitHub MCP :8020"]
        PGMCP["PostgreSQL MCP :8030"]
        DockerMCP["Docker MCP :8040"]
    end

    subgraph Data["Persistence & Coordination"]
        PG[("PostgreSQL / RDS")]
        Q[("Qdrant")]
        Redis[("Redis / Streams")]
        RunHistory["Persistent Run History"]
    end

    subgraph Observe["Observability"]
        Prom["Prometheus"]
        Grafana["Grafana"]
        OTEL["OpenTelemetry Collector"]
        Tempo["Tempo"]
        CW["CloudWatch"]
    end

    Client --> ALB --> API

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
    API --> RunHistory

    Worker --> PG
    Scheduler --> PG
    Outbox --> Redis

    API --> Prom
    API --> OTEL
    OTEL --> Tempo
    Prom --> Grafana
    API --> CW
```

## 4. Core Agentic Runtime

```mermaid
flowchart LR
    Request["Request"]
    Router["Planner / Router"]
    Workflow["LangGraph Workflow"]
    Research["Research / RAG"]
    A2A["A2A Delegation"]
    MCP["MCP Tool Execution"]
    Review["Human Review"]
    Policy["Policy"]
    Eval["Evaluation"]
    Result["Result"]

    Request --> Router
    Router --> Workflow
    Workflow --> Policy
    Policy -->|ALLOW| Research
    Policy -->|ALLOW| A2A
    Policy -->|ALLOW| MCP
    Policy -->|REVIEW| Review
    Review --> Workflow

    Research --> Eval
    A2A --> Eval
    MCP --> Eval
    Eval --> Result
```

MCP and A2A remain intentionally distinct:

- **MCP** is the structured tool boundary.
- **A2A** is the specialist-agent delegation boundary.

## 5. Governed Execution Boundary

```mermaid
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

Governance is runtime state. Approval is explicit. A successful plan does not imply permission to execute a destructive action.

## 6. Production Operations and Recovery

```mermaid
flowchart LR
    Detect["Detect Incident"]
    Persist["Persist Incident"]
    Diagnose["Ops Agent Diagnosis"]
    Action["Remediation Proposal"]
    Policy["Policy Decision"]
    HITL["Human Approval"]
    Execute["Controlled Execution"]
    Verify["Recovery Verification"]
    Close["Recovered / Closed"]
    Fail["Fail Closed"]

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

Recovery is successful only after verification.

## 7. Self-Healing Multi-Agent Runtime

```text
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

Key invariants:

- failed agents cannot replace themselves
- high-risk failover remains approval-aware
- replacement execution is verification-gated
- duplicate failover is idempotent
- checkpoint state persists across restart
- rejoin requires healthy state

## 8. Adaptive Governance

```mermaid
flowchart LR
    Signals["Runtime Signals"]
    History["Historical Aggregation"]
    Recommend["Recommendation"]
    Risk["Risk / Confidence"]
    Proposal["Versioned Proposal"]
    Review["Human Review"]
    Shadow["Shadow Evaluation"]
    Apply["Explicit Apply"]
    Rollback["Rollback"]

    Signals --> History --> Recommend --> Risk --> Proposal
    Proposal --> Review --> Shadow --> Apply --> Rollback
```

Adaptive governance recommends changes; it does not silently apply them.

## 9. Security and Compliance Evidence

```text
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

## 10. Continuous Evaluation

```text
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

Evaluation precedes rollout.

## 11. Enterprise Integration Governance

```text
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

## 12. Trusted Agent Registry

```text
identity
-> signed manifest
-> provenance
-> declared capabilities
-> health
-> governance compatibility
-> policy profile
-> trust score/state
-> routing boundary
```

Trust is not equivalent to registration.

## 13. Persistent Run History

```mermaid
flowchart LR
    Runtime["Governed Runtime"]
    History["Run History Repository"]
    DB[("PostgreSQL")]
    API["Run History API"]
    UI["Control Plane Run History"]

    Runtime --> History --> DB --> API --> UI
```

Persisted evidence includes runs, traces, primary/fallback agents, recovery evidence, latency, evaluation scores, and summary aggregation.

## 14. Microsoft Enterprise Integration Readiness

```mermaid
flowchart LR
    RedPA["RedPA Governed Runtime"]
    Contract["Microsoft Integration Contract"]
    PA["Power Automate"]
    Human["Human Approval"]
    Action["Governed RedPA Action"]
    Audit[("Audit Evidence")]

    RedPA --> Contract --> PA --> Human --> Action --> Audit
```

This is contract/readiness support. It does not claim a live tenant connection.

## 15. Enterprise Analytics

```mermaid
flowchart LR
    History[("Run History")]
    Analytics["Enterprise Analytics API"]
    KPI["Operational KPI Summary"]
    JSON["Power BI-friendly JSON"]
    CSV["Excel-compatible CSV"]

    History --> Analytics
    Analytics --> KPI
    Analytics --> JSON
    Analytics --> CSV
```

## 16. AWS Production Runtime Architecture — v20.0

```mermaid
flowchart TB
    Internet["Internet"]

    subgraph AWS["AWS eu-central-1 / prod stack"]
        ALB["Application Load Balancer :80"]
        ALBSG["ALB Security Group"]
        ECR["Amazon ECR / v20.0.0"]
        Secrets["AWS Secrets Manager"]
        RDS[("Private RDS PostgreSQL")]
        Logs["CloudWatch Logs"]
        Alarms["7 CloudWatch Alarms"]
        SNS["SNS production alert topic"]
        Scaling["Application Auto Scaling
min 2 / max 4"]
        Insights["ECS Container Insights"]
        Pulumi["Pulumi prod stack"]

        subgraph ECS["ECS / Fargate service"]
            TaskA["Backend + Redis sidecar"]
            TaskB["Backend + Redis sidecar"]
            Extra["Scale-out tasks up to 4"]
        end
    end

    Internet --> ALB --> ALBSG
    ALBSG -->|backend :8000 only| TaskA
    ALBSG -->|backend :8000 only| TaskB
    ECR --> TaskA
    ECR --> TaskB
    Secrets --> TaskA
    Secrets --> TaskB
    TaskA --> RDS
    TaskB --> RDS
    Scaling -. controls desired count .-> ECS
    Alarms --> SNS
    Alarms -. monitors .-> ECS
    Alarms -. monitors .-> ALB
    Alarms -. monitors .-> RDS
    ECS --> Logs
    ECS --> Insights
    Pulumi -. manages .-> AWS
```

### Validated production properties

- dedicated Pulumi `prod` stack, separate from the preserved `dev` stack
- production-specific physical resource identities
- ALB as the public application entry point
- backend port `8000` restricted to the ALB security group path
- two-task steady-state ECS service
- target-tracking ECS autoscaling from 2 to 4 tasks
- CPU target 60% and memory target 70%
- deployment circuit breaker and rollback behavior retained
- private encrypted RDS with deletion protection
- production secrets supplied through Pulumi/AWS secret boundaries
- ECR release image `v20.0.0` promoted from the validated RC artifact
- seven CloudWatch alarms with SNS alarm actions
- final production Pulumi preview: `39 unchanged`

HTTPS/custom-domain ingress, ACM, Route53 production DNS, WAF, Multi-AZ RDS, regional failover, multi-region HA, and an SLA/SLO are not claimed by V20.

## 17. Production Runtime and Release Validation

V20 validated the production startup and rollout path before final release publication:

```text
container startup:          PASS
/api/v1/platform/live:      healthy
runtime version:            20.0.0
environment:                production
ECS desired/running:        2/2
ECS pending:                0
rollout:                    COMPLETED
failed tasks:               0
Pulumi final state:         39 unchanged
```

The production startup contract includes explicit `ALLOWED_HOSTS`, production-strength secret configuration, URL-safe database credentials, and a liveness path that does not depend on Redis-backed rate limiting.

## 18. Database Recovery Boundary

Production RDS is private, storage-encrypted, deletion-protected, and configured with automated backup retention. The committed V20 production configuration keeps:

```text
Multi-AZ:             false
Backup retention:     1 day
Public access:        false
Storage encryption:   enabled
Deletion protection:  enabled
```

These are explicit deployment boundaries. V20 does not claim multi-AZ database HA or regional disaster recovery.

## 19. AWS Observability, Alerting, and Scaling

Seven CloudWatch alarms cover:

1. ECS CPU high
2. ECS memory high
3. ALB unhealthy host
4. ALB target 5xx
5. ALB response time
6. RDS CPU high
7. RDS low storage

In production, alarm actions route to the `redpa-prod-v20-alerts` SNS topic. Email subscription is optional and only created when `alert_email` is configured; no active email subscriber is claimed by the committed production config.

ECS target-tracking scaling uses CPU and memory signals with a production capacity range of 2–4 tasks. CloudWatch Logs and ECS Container Insights remain part of the AWS observability boundary.

## 20. Application Observability

```text
application metrics -> Prometheus -> Grafana
application traces  -> OpenTelemetry Collector -> Tempo
application logs    -> structured/correlated runtime evidence
```

Evaluation, governance, operations, request, and recovery signals contribute to platform observability.

## 21. Persistence Model

PostgreSQL is the durable relational system of record for platform/runtime/governance state.

Qdrant provides vector retrieval and semantic memory.

Redis supports coordination, caching, event streams, and runtime messaging.

A key principle is that important governance/recovery state should survive process restart.

## 22. Event and Background Processing

The platform includes:

- transactional outbox/event APIs
- Outbox Publisher
- background worker
- scheduler
- Redis-backed coordination
- Redis Streams publication

This separates synchronous request processing from asynchronous platform work.

## 23. Security and Governance Boundaries

1. Authentication and tenancy/RBAC foundations
2. Policy enforcement
3. Human Review
4. MCP execution controls
5. Connector governance
6. Trusted-agent routing
7. fail-closed recovery
8. persisted audit/evidence
9. approval-aware side effects
10. verification-gated recovery

## 24. Deployment View

### Docker Compose

The strongest integrated local runtime target.

### AWS / Pulumi

Actually deployed and validated for V20.0.0 in a dedicated `prod` stack in `eu-central-1`; the `dev` stack remains separately managed.

Validated:

- ECS/Fargate
- ECR
- ALB
- private RDS
- Secrets Manager
- CloudWatch Logs
- CloudWatch Alarms
- Container Insights
- controlled ingress
- self-recovery
- backup/restore readiness
- SNS-backed alarm routing
- ECS target-tracking autoscaling (2–4 tasks)
- clean Pulumi state

### Kubernetes / Helm

Deployment/package path. Not a claim of a currently running production cluster.

### Azure / Pulumi

Infrastructure/reference path unless separately validated against a live subscription.

## 25. API Architecture

The API is versioned under `/api/v1`.

Important boundaries include:

```text
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
/api/v1/production-demo/v18.2
/api/v1/control-plane/v18.3/runs
/api/v1/analytics/v18.5/power-bi
/api/v1/analytics/v18.5/excel.csv
```

Additional routers cover authentication, users, conversations/messages, chat/LLM, documents/RAG, Human Review, MCP, tools, agents, memory, evaluations, guardrails, policy enforcement, tenants, OAuth, events, analytics, connectors, model gateway, monitoring, and health.

## 26. Release Validation Boundary

Validated V20.0.0 evidence:

```text
Full regression:             437 passed
Live AWS runtime:            20.0.0 / production
ECS service:                 desired 2 / running 2 / pending 0
ECS rollout:                 COMPLETED
ECS autoscaling:             min 2 / max 4
ALB liveness:                healthy
RDS:                         private + encrypted + deletion-protected
SNS alert topic:             deployed
CloudWatch alarm actions:    SNS-backed
Pulumi final state:          39 unchanged
Git release tag:             v20.0.0
```

This demonstrates the tested production deployment boundary. It does not imply HTTPS/custom-domain readiness, WAF protection, Multi-AZ database HA, regional failover, multi-region HA, or an SLA/SLO.

## 27. V19 → V20 Evolution

```text
V19.0–V19.3  AWS runtime and managed-data foundation
V19.4        controlled ALB ingress
V19.5        ECS/RDS resilience hardening
V19.6        infrastructure observability
V19.7        failure recovery + backup/readiness validation
V20.0        dedicated production stack
             -> production resource identities
             -> validated v20.0.0 ECR artifact
             -> 2-task production floor
             -> ECS target-tracking autoscaling to 4
             -> SNS-backed CloudWatch alarm routing
             -> production startup contract hardening
             -> 39-resource zero-drift final state
```

## 28. Architectural Principles

- Autonomous reasoning and autonomous permission are separate concerns.
- High-risk side effects require explicit governance boundaries.
- Durable state is preferred for workflow, governance, and recovery checkpoints.
- Failure handling must be idempotent and restart-safe.
- Recovery requires verification.
- Adaptive policy changes are recommendation-first and explicit-apply.
- External connectors and remote agents are trust boundaries.
- Evaluation precedes rollout.
- Observability and release evidence are part of the quality model.
- Deployment readiness is demonstrated through evidence.
- Cloud deployment is not represented as HA beyond what is actually validated.

## 29. Related Documentation

- `docs/architecture/c4.md`
- `docs/architecture/arc42.md`
- `docs/architecture/ddd.md`
- `docs/architecture/adr/`
- `docs/MCP_PLATFORM.md`
- `docs/A2A_PLATFORM.md`
- `docs/TOOL_RUNTIME.md`
- `docs/HUMAN_REVIEW.md`
- `docs/V10_GOVERNED_AGENT_RUNTIME.md`
- `docs/V12_SELF_HEALING_STAGE1_10.md`
- `docs/V13_ADAPTIVE_GOVERNANCE_STAGE1_10.md`
- `docs/V14_SECURITY_COMPLIANCE_STAGE1_10.md`
- `docs/V15_PRODUCTION_CLOUD_PLATFORM_STAGE1_10.md`
- `docs/V16_AGENT_EVALUATION_AND_CONTINUOUS_IMPROVEMENT_STAGE1_10.md`
- `docs/V17_ENTERPRISE_INTEGRATION_HUB_STAGE1_10.md`
- `docs/V18_TRUSTED_AGENT_REGISTRY_STAGE1_10.md`
- `docs/V18_1_PRODUCTION_HARDENING_STAGE1_10.md`
- `docs/V18_2_PRODUCTION_E2E_DEMO_STAGE1_10.md`
- `docs/V18_3_CONTROL_PLANE_RUN_HISTORY.md`
- `docs/V18_4_MICROSOFT_ENTERPRISE_INTEGRATION.md`
- `docs/V18_5_ENTERPRISE_ANALYTICS.md`
- `docs/V19_CLOUD_DEPLOYMENT_FOUNDATION.md`
- `docs/V20_ENTERPRISE_PRODUCTION.md`
- `docs/releases/V20.0.0.md`
- `docs/releases/V19.7.0.md`
