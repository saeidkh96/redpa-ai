from __future__ import annotations

import asyncio
from time import perf_counter
from typing import Any

from app.tools.http_base import BaseHTTPTool
from app.tools.schemas import ToolExecutionResult, ToolMetadata


class NewsTool(BaseHTTPTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="news",
            description=(
                "Returns current top stories from the official "
                "Hacker News API."
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
            limit = int(arguments.get("limit", 5))
            limit = max(1, min(limit, 10))

            ids_response = await self.http_client.get_json(
                url=(
                    "https://hacker-news.firebaseio.com/"
                    "v0/topstories.json"
                ),
                allowed_hosts={"firebaseio.com"},
            )

            if not isinstance(ids_response.data, list):
                raise ValueError(
                    "Hacker News returned an invalid story list."
                )

            story_ids = ids_response.data[:limit]

            async def fetch_story(story_id: int) -> dict[str, Any] | None:
                response = await self.http_client.get_json(
                    url=(
                        "https://hacker-news.firebaseio.com/"
                        f"v0/item/{int(story_id)}.json"
                    ),
                    allowed_hosts={"firebaseio.com"},
                )
                return (
                    response.data
                    if isinstance(response.data, dict)
                    else None
                )

            raw_stories = await asyncio.gather(
                *(fetch_story(story_id) for story_id in story_ids)
            )

            stories = []
            for story in raw_stories:
                if not story:
                    continue
                stories.append(
                    {
                        "id": story.get("id"),
                        "title": story.get("title"),
                        "url": story.get("url"),
                        "author": story.get("by"),
                        "score": story.get("score"),
                        "comments": story.get("descendants"),
                        "timestamp": story.get("time"),
                    }
                )

            return ToolExecutionResult(
                tool_name=self.metadata.name,
                success=True,
                result={
                    "stories": stories,
                    "count": len(stories),
                    "provider": "Hacker News",
                },
                error=None,
                execution_time_ms=self._elapsed_ms(started_at),
                metadata={"provider": "hacker_news"},
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
