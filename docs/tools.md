# Tool System

## Components

- `BaseTool`: common asynchronous interface.
- `ToolMetadata`: name, description, version, and approval requirement.
- `ToolRegistry`: centralized registration and lookup.
- `ToolService`: execution, logging, and structured results.
- `Tool Node`: selection, arguments, execution, and response formatting.

## Current Tools

### Calculator

Uses AST parsing and an allowlist of operations. It does not use `eval` and does not support arbitrary Python execution.

### DateTime

Uses `zoneinfo.ZoneInfo` and supports IANA time zones.

## Adding a Tool

1. Create a class under `backend/app/tools/`.
2. Inherit from `BaseTool`.
3. Implement `metadata`.
4. Implement `execute`.
5. Register it in `registry.py`.
6. Add selection and argument extraction.
7. Add deterministic planner patterns when appropriate.
8. Add tests.
