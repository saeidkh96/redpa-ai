# Phase 4.3 Changelog

## Added

- deterministic Filesystem MCP intent extraction;
- dynamic tool-availability verification through UnifiedToolService;
- Planner-driven MCP tool routing;
- MCP execution through the LangGraph Tool Node;
- Python formatting for filesystem MCP responses;
- MCP execution metadata in chat results;
- planner and formatter tests.

## Supported chat requests

- list project files;
- read a project text file;
- search project source text;
- retrieve safe file metadata.

## Deferred

- generic LLM selection across arbitrary MCP servers;
- multi-tool plans;
- persistent HumanReview creation for MCP write tools.
