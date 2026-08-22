# Roadmap

This roadmap reflects implemented repository capabilities through RedPA AI v20.0.0. Historical phase documents remain the detailed evidence source for each milestone.

## Phase 1 — Core Platform
**Status: Complete**

FastAPI, PostgreSQL, JWT, users, conversations, messages, and Docker.

## Phase 2 — Agent Workflows
**Status: Complete**

LangGraph, planner, Chat, RAG, and document ingestion.

## Phase 3 — Research and Review
**Status: Complete**

Web research, evidence ranking, source synthesis, Human Review, resume, and monitoring.

## Phase 4 — MCP Platform
**Status: Complete**

MCP manager, registry, catalog, dynamic selection, filesystem/GitHub/PostgreSQL/Docker MCP services, planner integration, and execution policies.

## Phase 5 — Agent-to-Agent Platform
**Status: Complete**

Agent Registry and Agent Cards, capability discovery, A2A server/client boundaries, coordinator and specialist agents, delegation, parallel workflows, aggregation, metrics, and approval-aware routing.

## Phase 6 — Durable / Long-Running Workflows
**Status: Implemented**

The repository contains durable/distributed workflow, persisted execution state, retry/recovery, background processing, checkpoint, and resumable execution capabilities. Detailed behavior remains governed by the relevant runtime and phase documentation.

## Phase 7 — Agent Memory
**Status: Implemented**

The repository contains agent-memory and retrieval foundations spanning contextual/semantic retrieval, durable state, and memory-aware agent workflows. Retention and governance boundaries remain explicit.

## Phase 8 — Production Deployment
**Status: Implemented and AWS-production validated in v20.0.0**

V20 validates a dedicated AWS production Pulumi stack with ECS/Fargate, ECR, ALB, private encrypted RDS, Secrets Manager, CloudWatch, SNS-backed alarm routing, and ECS target-tracking autoscaling from 2 to 4 tasks.

Current boundaries include HTTP ALB ingress without a custom domain/ACM, single-AZ RDS, one-day backup retention, and no claim of regional or multi-region HA.

## Continuing Work

Future work should deepen validated production guarantees rather than relabel already-implemented phases. Candidate areas include HTTPS/custom-domain ingress, WAF, stronger database HA/recovery, explicit SLOs, production load testing, and broader live validation of non-AWS deployment paths.
