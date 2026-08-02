import pytest

from app.schemas.unified_tool import UnifiedToolInfo
from app.services.dynamic_mcp_selector import (
    DynamicMCPSelector,
)


def test_argument_validation_rejects_missing_required() -> None:
    tool = UnifiedToolInfo(
        qualified_name="mcp:example:search",
        source="mcp",
        name="search",
        display_name="Search",
        description="Search records.",
        version=None,
        server_name="example",
        requires_approval=False,
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                },
            },
            "required": [
                "query",
            ],
        },
    )

    with pytest.raises(
        ValueError,
    ):
        DynamicMCPSelector._validate_arguments(
            tool=tool,
            arguments={},
        )


def test_argument_validation_accepts_valid_arguments() -> None:
    tool = UnifiedToolInfo(
        qualified_name="mcp:example:search",
        source="mcp",
        name="search",
        display_name="Search",
        description="Search records.",
        version=None,
        server_name="example",
        requires_approval=False,
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                },
            },
            "required": [
                "query",
            ],
        },
    )

    DynamicMCPSelector._validate_arguments(
        tool=tool,
        arguments={
            "query": "LangGraph",
        },
    )
