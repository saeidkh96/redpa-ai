from __future__ import annotations

from prometheus_client import Counter, Histogram

AI_RUNTIME_REQUESTS = Counter("redpa_ai_runtime_requests_total", "Production AI runtime requests.", ("agent", "outcome"))
AI_RUNTIME_LATENCY = Histogram("redpa_ai_runtime_latency_seconds", "Production AI runtime latency.", ("agent", "provider"))
AI_RUNTIME_COST = Counter("redpa_ai_runtime_cost_usd_total", "Production AI runtime cost.", ("agent", "provider", "model"))
AI_GUARDRAIL_DECISIONS = Counter("redpa_ai_guardrail_decisions_total", "Production AI guardrail decisions.", ("stage", "decision"))
AI_TOOL_CALLS = Counter("redpa_ai_tool_calls_total", "Production AI tool calls.", ("source", "status"))
