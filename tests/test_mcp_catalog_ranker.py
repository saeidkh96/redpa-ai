from app.schemas.unified_tool import UnifiedToolInfo
from app.services.mcp_catalog_ranker import (
    MCPCatalogRanker,
)


def test_ranker_prefers_matching_tool() -> None:
    tools = [
        UnifiedToolInfo(
            qualified_name="mcp:github:create_issue",
            source="mcp",
            name="create_issue",
            display_name="Create issue",
            description="Create a GitHub issue.",
            version=None,
            server_name="github",
            requires_approval=True,
            input_schema={
                "type": "object",
                "properties": {
                    "repository": {
                        "type": "string",
                    },
                    "title": {
                        "type": "string",
                    },
                },
            },
        ),
        UnifiedToolInfo(
            qualified_name="mcp:filesystem:read_file",
            source="mcp",
            name="read_file",
            display_name="Read file",
            description="Read a text file.",
            version=None,
            server_name="filesystem",
            requires_approval=False,
            input_schema={},
        ),
    ]

    ranked = MCPCatalogRanker.shortlist(
        user_message=(
            "Create a GitHub issue in my repository"
        ),
        tools=tools,
    )

    assert ranked
    assert ranked[0].tool.qualified_name == (
        "mcp:github:create_issue"
    )
