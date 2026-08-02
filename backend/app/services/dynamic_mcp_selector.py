from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
)

from app.core.exceptions import (
    LLMInvalidResponseError,
    LLMServiceError,
)
from app.schemas.ollama import OllamaChatMessage
from app.schemas.unified_tool import UnifiedToolInfo
from app.services.llm_service import llm_service
from app.services.mcp_catalog_ranker import (
    MCPCatalogRanker,
    RankedMCPTool,
)
from app.services.unified_tool_service import (
    UnifiedToolService,
)


logger = logging.getLogger(__name__)


DYNAMIC_MCP_SELECTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "selected",
        "qualified_name",
        "arguments",
        "confidence",
        "reasoning",
    ],
    "properties": {
        "selected": {
            "type": "boolean",
        },
        "qualified_name": {
            "type": [
                "string",
                "null",
            ],
        },
        "arguments": {
            "type": "object",
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
        },
        "reasoning": {
            "type": "string",
        },
    },
}


class DynamicMCPSelection(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    selected: bool
    qualified_name: str | None = None
    arguments: dict[str, Any] = Field(
        default_factory=dict,
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )
    reasoning: str = Field(
        min_length=1,
        max_length=800,
    )


class DynamicMCPSelector:
    """
    Select an arbitrary MCP tool from the live Unified Tool Catalog.

    A deterministic ranker first limits the model context. The LLM may
    select only one of the supplied qualified names and must provide
    arguments matching the selected tool schema.
    """

    MIN_RANK_SCORE = 1.5
    MIN_SELECTION_CONFIDENCE = 0.65

    @classmethod
    async def select(
        cls,
        *,
        user_message: str,
    ) -> DynamicMCPSelection | None:
        catalog = await UnifiedToolService.get_catalog()

        mcp_tools = [
            item
            for item in catalog.items
            if item.source == "mcp"
        ]

        if not mcp_tools:
            return None

        shortlist = MCPCatalogRanker.shortlist(
            user_message=user_message,
            tools=mcp_tools,
            limit=8,
        )

        if (
            not shortlist
            or shortlist[0].score
            < cls.MIN_RANK_SCORE
        ):
            return None

        try:
            selection = await cls._select_with_llm(
                user_message=user_message,
                shortlist=shortlist,
            )
        except (
            LLMServiceError,
            LLMInvalidResponseError,
            ValidationError,
            ValueError,
            json.JSONDecodeError,
        ) as exception:
            logger.warning(
                "Dynamic MCP selection failed: %s",
                exception,
            )
            return None

        if not selection.selected:
            return None

        if selection.confidence < (
            cls.MIN_SELECTION_CONFIDENCE
        ):
            return None

        allowed_tools = {
            item.tool.qualified_name.casefold(): item.tool
            for item in shortlist
        }

        normalized_name = str(
            selection.qualified_name
            or ""
        ).casefold()

        selected_tool = allowed_tools.get(
            normalized_name,
        )

        if selected_tool is None:
            return None

        cls._validate_arguments(
            tool=selected_tool,
            arguments=selection.arguments,
        )

        return selection.model_copy(
            update={
                "qualified_name": (
                    selected_tool.qualified_name
                ),
            }
        )

    @classmethod
    async def _select_with_llm(
        cls,
        *,
        user_message: str,
        shortlist: list[RankedMCPTool],
    ) -> DynamicMCPSelection:
        tool_payload = [
            {
                "qualified_name": (
                    item.tool.qualified_name
                ),
                "server_name": (
                    item.tool.server_name
                ),
                "name": item.tool.name,
                "description": (
                    item.tool.description
                    or ""
                )[:1200],
                "requires_approval": (
                    item.tool.requires_approval
                ),
                "input_schema": (
                    item.tool.input_schema
                ),
                "rank_score": item.score,
                "matched_terms": list(
                    item.matched_terms,
                ),
            }
            for item in shortlist
        ]

        system_prompt = (
            "You select at most one MCP tool for a user request. "
            "Use only the supplied catalog. Never invent a tool or "
            "argument. Select false when no tool clearly satisfies "
            "the request. The qualified_name must exactly match one "
            "catalog item. Arguments must follow that tool's JSON "
            "schema. Return only the required JSON object."
        )

        user_prompt = (
            "USER_REQUEST:\n"
            f"{user_message}\n\n"
            "MCP_TOOL_CATALOG_JSON:\n"
            f"{json.dumps(tool_payload, ensure_ascii=False)}"
        )

        response = await llm_service.generate(
            messages=[
                OllamaChatMessage(
                    role="system",
                    content=system_prompt,
                ),
                OllamaChatMessage(
                    role="user",
                    content=user_prompt,
                ),
            ],
            response_format=(
                DYNAMIC_MCP_SELECTION_SCHEMA
            ),
            temperature=0.0,
        )

        raw_content = (
            response.message.content.strip()
        )

        if not raw_content:
            raise LLMInvalidResponseError(
                "Dynamic MCP selector returned an empty response."
            )

        parsed = json.loads(
            raw_content,
        )

        return DynamicMCPSelection.model_validate(
            parsed,
        )

    @staticmethod
    def _validate_arguments(
        *,
        tool: UnifiedToolInfo,
        arguments: dict[str, Any],
    ) -> None:
        if not isinstance(
            arguments,
            dict,
        ):
            raise ValueError(
                "MCP tool arguments must be an object."
            )

        schema = tool.input_schema

        if not isinstance(
            schema,
            dict,
        ):
            return

        properties = schema.get(
            "properties",
            {},
        )

        if not isinstance(
            properties,
            dict,
        ):
            properties = {}

        required = schema.get(
            "required",
            [],
        )

        if not isinstance(
            required,
            list,
        ):
            required = []

        missing = [
            name
            for name in required
            if name not in arguments
        ]

        if missing:
            raise ValueError(
                "Missing required MCP arguments: "
                + ", ".join(
                    str(
                        name,
                    )
                    for name in missing
                )
            )

        unknown = [
            name
            for name in arguments
            if name not in properties
        ]

        if unknown and properties:
            raise ValueError(
                "Unknown MCP arguments: "
                + ", ".join(
                    unknown,
                )
            )
