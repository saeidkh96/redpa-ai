# Agent Workflows

## Chat

```text
Planner → Chat Node → Ollama → Response Node
```

## RAG

```text
Planner → RAG Node → Retriever → Context Builder → LLM → Response
```

## Tool

```text
Planner → Tool Node → Registry → Tool Service → Tool
        → Response Formatter → Response
```

## Human Review

```text
Safety Gate → Human Review → Approve or Reject → Resume
```

## Planned Routes

`research` and `sql` remain planned capabilities and should return clear unsupported-capability responses until implemented.
