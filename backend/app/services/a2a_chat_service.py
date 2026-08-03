from __future__ import annotations

import json
import re
from typing import Any

from app.a2a_remote.bootstrap import RemoteAgentBootstrapService
from app.a2a_remote.client import RemoteA2AClient, RemoteA2AError
from app.a2a_remote.registry import (
    RemoteAgentRecord,
    remote_agent_registry,
)


class A2AChatService:
    @classmethod
    async def delegate(
        cls,
        user_message: str,
    ) -> dict[str, Any]:
        await RemoteAgentBootstrapService.ensure_defaults()

        records = await remote_agent_registry.list()
        available = [
            record
            for record in records
            if record.enabled
        ]

        if not available:
            return cls._failure(
                response_content=(
                    "No enabled remote A2A agent is available."
                ),
                error="No enabled remote A2A agent.",
            )

        selected, selection = cls.select_remote_agent(
            user_message=user_message,
            records=available,
        )

        try:
            delegation = await RemoteA2AClient.delegate(
                selected,
                user_message,
                timeout_seconds=60.0,
            )
        except RemoteA2AError as exception:
            return cls._failure(
                response_content=(
                    "The selected remote A2A agent could not complete the "
                    f"request. Reason: {exception}"
                ),
                error=str(exception),
                remote_agent=selected.name,
                base_url=selected.base_url,
                selection=selection,
            )

        task_payload = cls._extract_task_payload(
            delegation.final_response,
        )

        response_content = cls._extract_artifact_text(
            task_payload,
        )

        if not response_content:
            response_content = (
                "The remote A2A agent completed the task but returned "
                "no text artifact."
            )

        return {
            "success": delegation.success,
            "response_content": response_content,
            "remote_agent": selected.name,
            "base_url": selected.base_url,
            "selected_skill": selection.get("selected_skill"),
            "selection_score": selection.get("score", 0.0),
            "selection_terms": selection.get("matched_terms", []),
            "task_id": cls._optional_string(
                task_payload.get("id"),
            ),
            "context_id": cls._optional_string(
                task_payload.get("context_id"),
            ),
            "execution_time_ms": delegation.execution_time_ms,
            "event_count": delegation.event_count,
            "error": delegation.error,
        }

    @classmethod
    def select_remote_agent(
        cls,
        *,
        user_message: str,
        records: list[RemoteAgentRecord],
    ) -> tuple[RemoteAgentRecord, dict[str, Any]]:
        query_terms = cls._tokenize(user_message)

        ranked: list[
            tuple[
                float,
                str,
                RemoteAgentRecord,
                str | None,
                list[str],
            ]
        ] = []

        for record in records:
            card = record.card
            record_score = 0.0
            selected_skill: str | None = None
            selected_terms: list[str] = []

            agent_name = str(
                getattr(card, "name", record.name)
                or record.name
            )
            agent_description = str(
                getattr(card, "description", "")
                or ""
            )

            agent_terms = cls._tokenize(
                " ".join(
                    [
                        record.name,
                        agent_name,
                        agent_description,
                    ]
                )
            )

            record_score += len(
                query_terms & agent_terms,
            ) * 2.0

            skills = getattr(
                card,
                "skills",
                [],
            ) or []

            for skill in skills:
                skill_id = str(
                    getattr(skill, "id", "")
                    or ""
                )
                skill_name = str(
                    getattr(skill, "name", "")
                    or ""
                )
                description = str(
                    getattr(skill, "description", "")
                    or ""
                )
                tags = [
                    str(tag)
                    for tag in (
                        getattr(skill, "tags", [])
                        or []
                    )
                ]
                examples = [
                    str(example)
                    for example in (
                        getattr(skill, "examples", [])
                        or []
                    )
                ]

                name_terms = cls._tokenize(
                    " ".join(
                        [
                            skill_id,
                            skill_name,
                        ]
                    )
                )
                tag_terms = cls._tokenize(
                    " ".join(tags)
                )
                context_terms = cls._tokenize(
                    " ".join(
                        [
                            description,
                            *examples,
                        ]
                    )
                )

                name_matches = query_terms & name_terms
                tag_matches = query_terms & tag_terms
                context_matches = query_terms & context_terms

                skill_score = (
                    len(name_matches) * 5.0
                    + len(tag_matches) * 3.0
                    + len(context_matches) * 1.0
                )

                if skill_score > record_score:
                    record_score = skill_score
                    selected_skill = (
                        skill_id
                        or skill_name
                        or None
                    )
                    selected_terms = sorted(
                        name_matches
                        | tag_matches
                        | context_matches
                    )

            if record.connected:
                record_score += 0.25

            ranked.append(
                (
                    record_score,
                    record.name,
                    record,
                    selected_skill,
                    selected_terms,
                )
            )

        ranked.sort(
            key=lambda item: (
                -item[0],
                item[1],
            )
        )

        (
            score,
            _,
            selected_record,
            selected_skill,
            selected_terms,
        ) = ranked[0]

        return (
            selected_record,
            {
                "selected_skill": selected_skill,
                "score": round(score, 2),
                "matched_terms": selected_terms,
            },
        )

    @staticmethod
    def _tokenize(
        value: str,
    ) -> set[str]:
        stop_words = {
            "a",
            "an",
            "and",
            "can",
            "for",
            "from",
            "in",
            "is",
            "of",
            "on",
            "the",
            "to",
            "what",
            "which",
            "who",
            "with",
        }

        return {
            token
            for token in re.findall(
                r"[a-z0-9_]{2,}",
                str(value or "").casefold(),
            )
            if token not in stop_words
        }

    @staticmethod
    def _extract_task_payload(
        final_response: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not isinstance(final_response, dict):
            return {}

        task = final_response.get("task")

        return task if isinstance(task, dict) else final_response

    @classmethod
    def _extract_artifact_text(
        cls,
        task_payload: dict[str, Any],
    ) -> str:
        artifacts = task_payload.get(
            "artifacts",
            [],
        )

        if not isinstance(artifacts, list):
            return ""

        texts: list[str] = []

        for artifact in artifacts:
            if not isinstance(artifact, dict):
                continue

            parts = artifact.get(
                "parts",
                [],
            )

            if not isinstance(parts, list):
                continue

            for part in parts:
                if not isinstance(part, dict):
                    continue

                text = cls._optional_string(
                    part.get("text"),
                )

                if text:
                    texts.append(
                        cls._prettify_text(text)
                    )

        return "\n\n".join(texts).strip()

    @staticmethod
    def _prettify_text(
        value: str,
    ) -> str:
        stripped = value.strip()

        if (
            stripped.startswith("{")
            or stripped.startswith("[")
        ):
            try:
                return json.dumps(
                    json.loads(stripped),
                    ensure_ascii=False,
                    indent=2,
                )
            except json.JSONDecodeError:
                return stripped

        return stripped

    @staticmethod
    def _optional_string(
        value: Any,
    ) -> str | None:
        if value is None:
            return None

        normalized = str(value).strip()
        return normalized or None

    @staticmethod
    def _failure(
        *,
        response_content: str,
        error: str,
        remote_agent: str | None = None,
        base_url: str | None = None,
        selection: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        selection = selection or {}

        return {
            "success": False,
            "response_content": response_content,
            "remote_agent": remote_agent,
            "base_url": base_url,
            "selected_skill": selection.get(
                "selected_skill",
            ),
            "selection_score": selection.get(
                "score",
                0.0,
            ),
            "selection_terms": selection.get(
                "matched_terms",
                [],
            ),
            "task_id": None,
            "context_id": None,
            "execution_time_ms": 0.0,
            "event_count": 0,
            "error": error,
        }
