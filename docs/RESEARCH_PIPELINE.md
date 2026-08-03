# Research Pipeline

## Purpose

The Research workflow retrieves current web evidence and produces a source-grounded synthesis.

## Stages

1. query preparation;
2. web search;
3. evidence normalization;
4. duplicate removal;
5. ranking;
6. bounded context construction;
7. model synthesis;
8. metadata persistence.

## Reliability

The implementation separates search failures from model failures and records evidence metadata for inspection.

## Current Search Provider

Public web search is performed through DDGS without requiring a paid API key.

## Relationship to A2A

The built-in Research Agent publishes the `web_research` capability in the internal Agent Registry.

An A2A discovery request such as:

```text
Find an agent for web research and evidence
```

returns the Research Agent as the strongest capability match.

## Current Limitation

The current A2A Coordinator discovers the Research Agent capability but does not yet run an independent remote Research Agent service.

Research execution still occurs through the local LangGraph Research workflow.

Independent specialist Remote Agents are planned for a later phase.
