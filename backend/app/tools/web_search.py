from __future__ import annotations

import os
from time import perf_counter
from typing import Any

from app.tools.http_base import BaseHTTPTool
from app.tools.schemas import ToolExecutionResult, ToolMetadata


class WebSearchTool(BaseHTTPTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="web_search",
            description=(
                "Searches the public web through the Brave Search API."
            ),
            version="1.0.0",
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
            count = int(arguments.get("count", 5))
            count = max(1, min(count, 10))

            api_key = os.getenv(
                "BRAVE_SEARCH_API_KEY",
                "",
            ).strip()

            if not api_key:
                raise ValueError(
                    "BRAVE_SEARCH_API_KEY is not configured."
                )

            response = await self.http_client.get_json(
                url="https://api.search.brave.com/res/v1/web/search",
                params={
                    "q": query,
                    "count": count,
                    "safesearch": "moderate",
                    "text_decorations": "false",
                },
                headers={
                    "X-Subscription-Token": api_key,
                },
                allowed_hosts={"api.search.brave.com"},
            )

            web = (
                response.data.get("web", {})
                if isinstance(response.data, dict)
                else {}
            )
            raw_results = (
                web.get("results", [])
                if isinstance(web, dict)
                else []
            )

            results = []
            for item in raw_results[:count]:
                if not isinstance(item, dict):
                    continue
                results.append(
                    {
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "description": item.get("description"),
                        "age": item.get("age"),
                    }
                )

            return ToolExecutionResult(
                tool_name=self.metadata.name,
                success=True,
                result={
                    "query": query,
                    "results": results,
                    "count": len(results),
                    "provider": "Brave Search",
                },
                error=None,
                execution_time_ms=self._elapsed_ms(started_at),
                metadata={"provider": "brave_search"},
            )

        except Exception as exception:
            return ToolExecutionResult(
                tool_name=self.metadata.name,
                success=False,
                result=None,
                error=f"{type(exception).__name__}: {exception}"[:1000],
                execution_time_ms=self._elapsed_ms(started_at),
                metadata={
                    "error_type": type(exception).__name__,
                },
            )

    @staticmethod
    def _elapsed_ms(started_at: float) -> float:
        return round((perf_counter() - started_at) * 1000, 2)
