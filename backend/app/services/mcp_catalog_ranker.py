from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas.unified_tool import UnifiedToolInfo


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "can",
    "do",
    "for",
    "from",
    "how",
    "i",
    "in",
    "inside",
    "is",
    "me",
    "of",
    "on",
    "please",
    "show",
    "the",
    "to",
    "what",
    "with",
    "you",
}


@dataclass(frozen=True, slots=True)
class RankedMCPTool:
    tool: UnifiedToolInfo
    score: float
    matched_terms: tuple[str, ...]


class MCPCatalogRanker:
    """Deterministically shortlist relevant MCP tools."""

    @classmethod
    def shortlist(
        cls,
        *,
        user_message: str,
        tools: list[UnifiedToolInfo],
        limit: int = 8,
    ) -> list[RankedMCPTool]:
        query_terms = cls._tokenize(
            user_message,
        )

        ranked: list[RankedMCPTool] = []

        for tool in tools:
            if tool.source != "mcp":
                continue

            tool_text = " ".join(
                filter(
                    None,
                    [
                        tool.qualified_name,
                        tool.name,
                        tool.display_name,
                        tool.description,
                        tool.server_name,
                        cls._schema_text(
                            tool.input_schema,
                        ),
                    ],
                )
            )

            tool_terms = cls._tokenize(
                tool_text,
            )

            common_terms = sorted(
                query_terms
                & tool_terms,
            )

            name_terms = cls._tokenize(
                " ".join(
                    filter(
                        None,
                        [
                            tool.name,
                            tool.display_name,
                        ],
                    )
                )
            )

            description_terms = cls._tokenize(
                tool.description
                or "",
            )

            name_overlap = len(
                query_terms
                & name_terms,
            )

            description_overlap = len(
                query_terms
                & description_terms,
            )

            exact_name_bonus = (
                3.0
                if tool.name.casefold()
                in user_message.casefold()
                else 0.0
            )

            server_bonus = (
                1.0
                if (
                    tool.server_name
                    and tool.server_name.casefold()
                    in user_message.casefold()
                )
                else 0.0
            )

            score = (
                name_overlap * 3.0
                + description_overlap * 1.5
                + len(common_terms) * 0.5
                + exact_name_bonus
                + server_bonus
            )

            if score <= 0:
                continue

            ranked.append(
                RankedMCPTool(
                    tool=tool,
                    score=score,
                    matched_terms=tuple(
                        common_terms[:12],
                    ),
                )
            )

        ranked.sort(
            key=lambda item: (
                -item.score,
                item.tool.qualified_name.casefold(),
            )
        )

        return ranked[
            : max(
                1,
                min(
                    int(limit),
                    12,
                ),
            )
        ]

    @staticmethod
    def _tokenize(
        value: str,
    ) -> set[str]:
        return {
            token
            for token in re.findall(
                r"[a-z0-9_]{2,}",
                str(
                    value
                    or "",
                ).casefold(),
            )
            if token not in STOP_WORDS
        }

    @classmethod
    def _schema_text(
        cls,
        schema: dict,
    ) -> str:
        properties = schema.get(
            "properties",
            {},
        )

        if not isinstance(
            properties,
            dict,
        ):
            return ""

        parts: list[str] = []

        for name, raw_property in properties.items():
            parts.append(
                str(
                    name,
                )
            )

            if isinstance(
                raw_property,
                dict,
            ):
                parts.extend(
                    str(
                        raw_property.get(
                            key,
                            "",
                        )
                    )
                    for key in (
                        "title",
                        "description",
                        "type",
                    )
                )

        return " ".join(
            parts,
        )
