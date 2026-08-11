# RedPA AI v4.2 — Production Agentic Systems Readiness

V4.2 directly targets the capabilities expected from teams building production-grade agentic AI products. It extends the existing v3 data plane and v4/v4.1 control plane rather than replacing them.

## 1. Multi-provider Model Gateway

RedPA now has first-class provider adapters for Ollama, OpenAI-compatible/OpenAI, Anthropic Claude, and Google Gemini. Providers remain disabled unless configured. Routing supports explicit selection, per-agent routes, capability routing, fallbacks, circuit breakers, retries, and a cost-aware strategy driven by `MODEL_GATEWAY_ECONOMICS_JSON`.

## 2. Unified Agent Runtime

`ProductionAgentRuntime` combines business rules, data context, guarded internal/MCP tool execution, model invocation, output guardrails, evaluation gates, concurrency control, and idempotency. The API is exposed at `POST /api/v1/production-ai/runtime/execute`.

## 3. Guardrails and Safety

The production runtime applies local input/output content guardrails in addition to the existing Spring Boot policy boundary. The local layer detects prompt-injection patterns and redacts common secrets and email addresses. Existing tool execution remains behind RedPA's policy/HITL boundary.

## 4. Evaluation Gates

Each runtime response receives a production evaluation outcome: `pass`, `retry`, `human_review`, or `block`. Latency and cost targets can participate in the gate. The existing persistent Evaluation Platform remains available for offline/online metric runs.

## 5. AI Observability

New Prometheus metrics cover runtime request outcomes, latency, cost, guardrail decisions, and tool calls. They complement the existing OpenTelemetry, Prometheus, Grafana, and Tempo stack.

## 6. Reliability and Scalability

V4.2 adds a concurrency gate, idempotency cache foundation, retry-budget primitive, and reuses the Model Gateway retry/timeout/circuit-breaker layer plus v4.1 durable workflows, checkpoints, outbox, DLQ, and replay.

## 7. Cost Efficiency

Cost-aware routing ranks capability-compatible providers using an economics catalog. Tenant provider allow-lists and token/cost budgets from v4.1 remain enforced by the production runtime API, and successful usage is persisted through Model Governance.

## Runtime API

- `GET /api/v1/production-ai/readiness`
- `POST /api/v1/production-ai/runtime/execute`

The runtime request can include tenant, agent, provider/model overrides, data context, business rules, internal/MCP tool calls, latency/cost targets, token limits, and an idempotency key.

## Safety note

Provider API keys must be supplied through environment/secrets management. No provider is enabled merely by adding this code. The local content guardrail is a deterministic first line of defense, not a replacement for the external policy service, HITL, or domain-specific safety evaluation.
