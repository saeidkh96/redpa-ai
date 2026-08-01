from __future__ import annotations

from functools import partial
from time import perf_counter
from typing import Any

import anyio
from ddgs import DDGS

from app.tools.http_base import BaseHTTPTool
from app.tools.schemas import (
    ToolExecutionResult,
    ToolMetadata,
)


class WebSearchTool(BaseHTTPTool):
    """
    Free web-search tool backed by DDGS.

    The public tool name remains `web_search`, so the Planner,
    ResearchService, Tool Registry, and response formatter do not
    require changes.
    """

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="web_search",
            description=(
                "Searches the public web without an API key using "
                "DDGS with DuckDuckGo as the preferred backend."
            ),
            version="2.0.0",
            requires_approval=False,
        )

    async def execute(
        self,
        arguments: dict[str, Any],
    ) -> ToolExecutionResult:
        started_at = perf_counter()

        try:
            query = self.required_string(
                arguments,
                "query",
                max_length=500,
            )

            count = self._parse_count(
                arguments.get(
                    "count",
                    5,
                )
            )

            region = self.optional_string(
                arguments,
                "region",
                default="wt-wt",
                max_length=20,
            ) or "wt-wt"

            safesearch = self.optional_string(
                arguments,
                "safesearch",
                default="moderate",
                max_length=20,
            ) or "moderate"

            if safesearch not in {
                "on",
                "moderate",
                "off",
            }:
                raise ValueError(
                    "'safesearch' must be one of: "
                    "on, moderate, off."
                )

            raw_results, backend_used = await self._search(
                query=query,
                count=count,
                region=region,
                safesearch=safesearch,
            )

            results = self._normalize_results(
                raw_results=raw_results,
                count=count,
            )

            return ToolExecutionResult(
                tool_name=self.metadata.name,
                success=True,
                result={
                    "query": query,
                    "results": results,
                    "count": len(results),
                    "provider": "DDGS",
                    "backend": backend_used,
                },
                error=None,
                execution_time_ms=self._elapsed_ms(
                    started_at,
                ),
                metadata={
                    "provider": "ddgs",
                    "backend": backend_used,
                    "api_key_required": False,
                },
            )

        except Exception as exception:
            return ToolExecutionResult(
                tool_name=self.metadata.name,
                success=False,
                result=None,
                error=(
                    f"{type(exception).__name__}: "
                    f"{exception}"
                )[:1000],
                execution_time_ms=self._elapsed_ms(
                    started_at,
                ),
                metadata={
                    "error_type": type(
                        exception,
                    ).__name__,
                    "provider": "ddgs",
                },
            )

    async def _search(
        self,
        *,
        query: str,
        count: int,
        region: str,
        safesearch: str,
    ) -> tuple[list[dict[str, Any]], str]:
        """
        Prefer DuckDuckGo and fall back to DDGS automatic backend
        selection if DuckDuckGo is temporarily unavailable.
        """

        try:
            results = await self._run_search_in_thread(
                query=query,
                count=count,
                region=region,
                safesearch=safesearch,
                backend="duckduckgo",
            )

            if results:
                return results, "duckduckgo"

        except Exception:
            # DDGS/search-engine throttling can be transient.
            # The automatic fallback remains free and requires no key.
            pass

        results = await self._run_search_in_thread(
            query=query,
            count=count,
            region=region,
            safesearch=safesearch,
            backend="auto",
        )

        return results, "auto"

    @staticmethod
    async def _run_search_in_thread(
        *,
        query: str,
        count: int,
        region: str,
        safesearch: str,
        backend: str,
    ) -> list[dict[str, Any]]:
        search_call = partial(
            WebSearchTool._search_sync,
            query=query,
            count=count,
            region=region,
            safesearch=safesearch,
            backend=backend,
        )

        return await anyio.to_thread.run_sync(
            search_call,
            abandon_on_cancel=True,
        )

    @staticmethod
    def _search_sync(
        *,
        query: str,
        count: int,
        region: str,
        safesearch: str,
        backend: str,
    ) -> list[dict[str, Any]]:
        client = DDGS(
            timeout=15,
        )

        raw_results = client.text(
            query=query,
            region=region,
            safesearch=safesearch,
            max_results=count,
            backend=backend,
        )

        if raw_results is None:
            return []

        return [
            item
            for item in raw_results
            if isinstance(
                item,
                dict,
            )
        ]

    @staticmethod
    def _normalize_results(
        *,
        raw_results: list[dict[str, Any]],
        count: int,
    ) -> list[dict[str, Any]]:
        normalized_results: list[
            dict[str, Any]
        ] = []

        seen_urls: set[str] = set()

        for item in raw_results:
            title = str(
                item.get(
                    "title",
                    "",
                )
                or ""
            ).strip()

            url = str(
                item.get(
                    "href",
                    item.get(
                        "url",
                        "",
                    ),
                )
                or ""
            ).strip()

            description = str(
                item.get(
                    "body",
                    item.get(
                        "description",
                        "",
                    ),
                )
                or ""
            ).strip()

            if not title or not url:
                continue

            normalized_url = url.casefold()

            if normalized_url in seen_urls:
                continue

            seen_urls.add(
                normalized_url,
            )

            normalized_results.append(
                {
                    "title": title,
                    "url": url,
                    "description": description,
                    "age": item.get(
                        "date",
                    ),
                }
            )

            if len(normalized_results) >= count:
                break

        return normalized_results

    @staticmethod
    def _parse_count(
        raw_count: Any,
    ) -> int:
        try:
            count = int(
                raw_count,
            )
        except (
            TypeError,
            ValueError,
        ) as exception:
            raise ValueError(
                "'count' must be an integer."
            ) from exception

        return max(
            1,
            min(
                count,
                10,
            ),
        )

    @staticmethod
    def _elapsed_ms(
        started_at: float,
    ) -> float:
        return round(
            (
                perf_counter()
                - started_at
            )
            * 1000,
            2,
        )
