from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from pydantic import ValidationError

from app.agents.prompts import PLANNER_SYSTEM_PROMPT
from app.agents.state import AgentRoute
from app.core.config import settings
from app.core.exceptions import (
    LLMInvalidResponseError,
    LLMServiceError,
)
from app.schemas.ollama import OllamaChatMessage
from app.schemas.planner import (
    PlannerExecutionResult,
    PlannerResult,
)
from app.services.llm_service import llm_service


logger = logging.getLogger(__name__)


PLANNER_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "route": {
            "type": "string",
            "enum": [
                "chat",
                "rag",
                "research",
                "tool",
                "sql",
                "human_review",
            ],
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
        },
        "reasoning": {
            "type": "string",
            "minLength": 1,
        },
        "signals": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
    },
    "required": [
        "route",
        "confidence",
        "reasoning",
        "signals",
    ],
    "additionalProperties": False,
}


ROUTE_PATTERNS: dict[
    AgentRoute,
    tuple[str, ...],
] = {
    "rag": (
        r"\buploaded\s+(document|documents|file|files|pdf|pdfs)\b",
        r"\bmy\s+(document|documents|file|files|pdf|pdfs)\b",
        r"\bsearch\s+(in|inside|through)\s+(the|my)\s+"
        r"(document|documents|file|files|pdf|pdfs)\b",
        r"\bretrieve\s+from\s+(the|my)\s+"
        r"(document|documents|file|files|pdf|pdfs)\b",
        r"\bknowledge[\s-]?base\b",
        r"\bvector\s+(database|store)\b",
    ),
    "research": (
        r"\bsearch\s+the\s+web\b",
        r"\bsearch\s+online\b",
        r"\bbrowse\s+the\s+web\b",
        r"\bfind\s+online\b",
        r"\blook\s+up\s+online\b",
        r"\bresearch\s+online\b",
        r"\blatest\s+(news|information|updates|developments)\b",
        r"\bcurrent\s+(news|information|updates|developments)\b",
        r"\brecent\s+(news|updates|developments)\b",
        r"\bexternal\s+sources\b",
        r"\bweb\s+research\b",
        r"\bonline\s+sources\b",
        r"\bprovide\s+(sources|citations)\b",
        r"\bwith\s+(sources|citations)\b",
        r"\bverify\s+(online|on\s+the\s+web)\b",
    ),
    "sql": (
        r"\bexecute\s+(this\s+)?sql\b",
        r"\brun\s+(this\s+)?(sql|query)\b",
        r"\bquery\s+the\s+database\b",
        r"\bquery\s+database\b",
        r"\bexecute\s+(a\s+)?database\s+query\b",
    ),
    "tool": (
        r"\bcalculate\b",
        r"\bcalculator\b",
        r"\bcompute\b",
        r"\bevaluate\s+(this\s+)?expression\b",
        r"\bsolve\s+(this\s+)?expression\b",
        r"\bwhat\s+is\s+[-+()0-9.\s*/%]+\??$",
        r"(?<![\w.])"
        r"[-+]?(?:\d+(?:\.\d+)?|\.\d+)"
        r"(?:\s*(?:\*\*|[+\-*/%])\s*"
        r"(?:\d+(?:\.\d+)?|\.\d+))+"
        r"(?![\w.])",
        r"\bwhat\s+time\s+is\s+it\b",
        r"\bcurrent\s+time\b",
        r"\btime\s+now\b",
        r"\btoday'?s\s+date\b",
        r"\bcurrent\s+date\b",
        r"\bwhat\s+date\s+is\s+it\b",
        r"\bwhat\s+day\s+is\s+it\b",
        r"\bdate\s+today\b",
        r"\btime\s+(?:in|for)\s+[a-z_/\-\s]+\b",
        r"\bdate\s+(?:in|for)\s+[a-z_/\-\s]+\b",
        r"\bday\s+(?:in|for)\s+[a-z_/\-\s]+\b",
        r"\bsend\s+(an?\s+)?email\b",
        r"\bemail\s+(him|her|them|someone|the\s+user)\b",
        r"\bcreate\s+(a\s+)?calendar\s+event\b",
        r"\bschedule\s+(a\s+)?meeting\b",
        r"\bcall\s+(an?\s+)?api\b",
        r"\bcreate\s+(a\s+)?github\s+issue\b",
        r"\bexecute\s+(the\s+)?tool\b",
        r"\buse\s+(the\s+)?tool\b",
        r"\bissue\s+(a\s+)?refund\b",
        r"\bprocess\s+(a\s+)?refund\b",
    ),
    "human_review": (
        r"\bhuman\s+review\b",
        r"\bhuman\s+approval\b",
        r"\bmanual\s+approval\b",
        r"\bmanager\s+approval\b",
        r"\breview\s+by\s+(a\s+)?human\b",
        r"\bescalate\s+to\s+(a\s+)?human\b",
        r"\bhuman[\s-]?in[\s-]?the[\s-]?loop\b",
    ),
}


ROUTE_PRIORITY: tuple[AgentRoute, ...] = (
    "human_review",
    "tool",
    "sql",
    "rag",
    "research",
)


DETERMINISTIC_CALCULATOR_PATTERNS: tuple[str, ...] = (
    r"\bcalculate\b",
    r"\bcalculator\b",
    r"\bcompute\b",
    r"\bevaluate\s+(this\s+)?expression\b",
    r"\bsolve\s+(this\s+)?expression\b",
    r"\bwhat\s+is\s+[-+()0-9.\s*/%]+\??$",
    r"(?<![\w.])"
    r"[-+]?(?:\d+(?:\.\d+)?|\.\d+)"
    r"(?:\s*(?:\*\*|[+\-*/%])\s*"
    r"(?:\d+(?:\.\d+)?|\.\d+))+"
    r"(?![\w.])",
)


DETERMINISTIC_DATETIME_PATTERNS: tuple[str, ...] = (
    r"\bwhat\s+time\s+is\s+it(?:\s+(?:in|for)\s+.+)?\??$",
    r"\bcurrent\s+time(?:\s+(?:in|for)\s+.+)?\??$",
    r"\btime\s+now(?:\s+(?:in|for)\s+.+)?\??$",
    r"\bwhat\s+is\s+the\s+time(?:\s+(?:in|for)\s+.+)?\??$",
    r"\bwhat\s+date\s+is\s+it(?:\s+(?:in|for)\s+.+)?\??$",
    r"\bwhat\s+day\s+is\s+it(?:\s+(?:in|for)\s+.+)?\??$",
    r"\btoday'?s\s+date(?:\s+(?:in|for)\s+.+)?\??$",
    r"\bcurrent\s+date(?:\s+(?:in|for)\s+.+)?\??$",
    r"\bdate\s+today(?:\s+(?:in|for)\s+.+)?\??$",
    r"\btime\s+(?:in|for)\s+[a-z_/\-\s]+\??$",
    r"\bdate\s+(?:in|for)\s+[a-z_/\-\s]+\??$",
    r"\bday\s+(?:in|for)\s+[a-z_/\-\s]+\??$",
)


class PlannerService:
    @classmethod
    async def create_plan(
        cls,
        user_message: str,
    ) -> PlannerExecutionResult:
        cleaned_message = user_message.strip()

        if not cleaned_message:
            raise ValueError(
                "Planner user message cannot be empty."
            )

        started_at = time.perf_counter()

        deterministic_plan = cls._create_deterministic_plan(
            user_message=cleaned_message,
        )

        if deterministic_plan is not None:
            latency_ms = (
                time.perf_counter() - started_at
            ) * 1000

            logger.info(
                "Deterministic planner selected route "
                "| route=%s confidence=%.2f signals=%s",
                deterministic_plan.route,
                deterministic_plan.confidence,
                deterministic_plan.signals,
            )

            return PlannerExecutionResult(
                plan=deterministic_plan,
                provider="rule_based",
                model="deterministic-router-v2",
                fallback_used=False,
                error=None,
                latency_ms=round(
                    latency_ms,
                    2,
                ),
            )

        try:
            llm_plan = await cls._create_llm_plan(
                user_message=cleaned_message,
            )

            normalized_plan = cls._normalize_llm_plan(
                user_message=cleaned_message,
                plan=llm_plan,
            )

            latency_ms = (
                time.perf_counter() - started_at
            ) * 1000

            return PlannerExecutionResult(
                plan=normalized_plan,
                provider="ollama",
                model=settings.ollama_model,
                fallback_used=False,
                error=None,
                latency_ms=round(
                    latency_ms,
                    2,
                ),
            )

        except Exception as exception:
            latency_ms = (
                time.perf_counter() - started_at
            ) * 1000

            error_message = cls._format_error(
                exception,
            )

            logger.warning(
                "LLM planner failed; using rule-based fallback "
                "| latency_ms=%.2f | error=%s",
                latency_ms,
                error_message,
            )

            fallback_plan = cls.create_rule_based_plan(
                user_message=cleaned_message,
            )

            return PlannerExecutionResult(
                plan=fallback_plan,
                provider="rule_based",
                model="deterministic-router-v2",
                fallback_used=True,
                error=error_message,
                latency_ms=round(
                    latency_ms,
                    2,
                ),
            )

    @classmethod
    def _create_deterministic_plan(
        cls,
        *,
        user_message: str,
    ) -> PlannerResult | None:
        """
        Handle requests that should not require an LLM decision.

        Calculator and current date/time requests are deterministic,
        cheaper, faster, and more reliable when routed directly.
        """

        normalized_message = cls._normalize_text(
            user_message,
        )

        calculator_signal = cls._match_first_pattern(
            value=normalized_message,
            patterns=DETERMINISTIC_CALCULATOR_PATTERNS,
        )

        if calculator_signal is not None:
            return PlannerResult(
                route="tool",
                confidence=1.0,
                reasoning=(
                    "Selected the 'tool' route because the request "
                    "contains a mathematical expression that can be "
                    "executed by the calculator tool."
                ),
                signals=[
                    calculator_signal,
                    "calculator",
                ],
            )

        datetime_signal = cls._match_first_pattern(
            value=normalized_message,
            patterns=DETERMINISTIC_DATETIME_PATTERNS,
        )

        if datetime_signal is not None:
            return PlannerResult(
                route="tool",
                confidence=1.0,
                reasoning=(
                    "Selected the 'tool' route because the request "
                    "asks for the current date or time, which must "
                    "be provided by the datetime tool instead of "
                    "being guessed by the language model."
                ),
                signals=[
                    datetime_signal,
                    "datetime",
                ],
            )

        return None

    @classmethod
    async def _create_llm_plan(
        cls,
        *,
        user_message: str,
    ) -> PlannerResult:
        messages = [
            OllamaChatMessage(
                role="system",
                content=PLANNER_SYSTEM_PROMPT,
            ),
            OllamaChatMessage(
                role="user",
                content=(
                    "Classify this request and return only the "
                    "required JSON object:\n\n"
                    f"{user_message}"
                ),
            ),
        ]

        response_parts: list[str] = []

        try:
            async for token in llm_service.stream_generate(
                messages=messages,
                response_format=PLANNER_JSON_SCHEMA,
                temperature=0.0,
            ):
                if token:
                    response_parts.append(token)

        except LLMServiceError:
            raise

        except Exception as exception:
            raise LLMInvalidResponseError(
                "The LLM planner request failed."
            ) from exception

        raw_response = "".join(
            response_parts,
        ).strip()

        if not raw_response:
            raise LLMInvalidResponseError(
                "The LLM planner returned an empty response."
            )

        logger.info(
            "Planner raw response | response=%s",
            raw_response,
        )

        parsed_response = cls._parse_json_response(
            raw_response,
        )

        try:
            return PlannerResult.model_validate(
                parsed_response,
            )

        except ValidationError as exception:
            raise LLMInvalidResponseError(
                "The LLM planner returned an invalid planning "
                f"result: {exception.errors()}"
            ) from exception

    @classmethod
    def _normalize_llm_plan(
        cls,
        *,
        user_message: str,
        plan: PlannerResult,
    ) -> PlannerResult:
        normalized_message = cls._normalize_text(
            user_message,
        )

        deterministic_plan = cls._create_deterministic_plan(
            user_message=user_message,
        )

        if deterministic_plan is not None:
            return deterministic_plan

        if plan.route == "research":
            has_explicit_research_signal = any(
                re.search(
                    pattern,
                    normalized_message,
                    flags=re.IGNORECASE,
                )
                is not None
                for pattern in ROUTE_PATTERNS["research"]
            )

            if not has_explicit_research_signal:
                logger.info(
                    "Planner route normalized | original_route=research "
                    "normalized_route=chat | reason=no explicit external "
                    "research signal"
                )

                return plan.model_copy(
                    update={
                        "route": "chat",
                        "confidence": max(
                            0.90,
                            plan.confidence,
                        ),
                        "reasoning": (
                            "The request is a general explanation or "
                            "knowledge question that can be answered by "
                            "the chat workflow and does not explicitly "
                            "require web browsing, current information, "
                            "external sources, or citations."
                        ),
                        "signals": [
                            "general explanation",
                            "no explicit external research request",
                        ],
                    }
                )

        if plan.route == "sql":
            has_explicit_sql_signal = any(
                re.search(
                    pattern,
                    normalized_message,
                    flags=re.IGNORECASE,
                )
                is not None
                for pattern in ROUTE_PATTERNS["sql"]
            )

            if not has_explicit_sql_signal:
                logger.info(
                    "Planner route normalized | original_route=sql "
                    "normalized_route=chat | reason=no explicit SQL signal"
                )

                return plan.model_copy(
                    update={
                        "route": "chat",
                        "confidence": max(
                            0.90,
                            plan.confidence,
                        ),
                        "reasoning": (
                            "The request does not explicitly ask to execute "
                            "SQL or query a database, so the SQL workflow "
                            "was rejected."
                        ),
                        "signals": [
                            "no explicit SQL request",
                        ],
                    }
                )

        return plan

    @staticmethod
    def create_rule_based_plan(
        *,
        user_message: str,
    ) -> PlannerResult:
        normalized_message = PlannerService._normalize_text(
            user_message,
        )

        deterministic_plan = PlannerService._create_deterministic_plan(
            user_message=user_message,
        )

        if deterministic_plan is not None:
            return deterministic_plan

        for route in ROUTE_PRIORITY:
            patterns = ROUTE_PATTERNS.get(
                route,
                (),
            )

            for pattern in patterns:
                match = re.search(
                    pattern,
                    normalized_message,
                    flags=re.IGNORECASE,
                )

                if match is None:
                    continue

                matched_signal = match.group(0).strip()

                return PlannerResult(
                    route=route,
                    confidence=0.75,
                    reasoning=(
                        f"The rule-based fallback selected "
                        f"the '{route}' route because the "
                        f"request matched '{matched_signal}'."
                    ),
                    signals=[
                        matched_signal,
                    ],
                )

        return PlannerResult(
            route="chat",
            confidence=0.65,
            reasoning=(
                "The rule-based fallback selected the "
                "'chat' route because no specialized "
                "execution or retrieval request was detected."
            ),
            signals=[],
        )

    @staticmethod
    def _match_first_pattern(
        *,
        value: str,
        patterns: tuple[str, ...],
    ) -> str | None:
        for pattern in patterns:
            match = re.search(
                pattern,
                value,
                flags=re.IGNORECASE,
            )

            if match is not None:
                return match.group(0).strip()

        return None

    @staticmethod
    def _parse_json_response(
        raw_response: str,
    ) -> dict[str, Any]:
        cleaned_response = raw_response.strip()

        cleaned_response = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned_response,
            flags=re.IGNORECASE,
        )

        cleaned_response = re.sub(
            r"\s*```$",
            "",
            cleaned_response,
        )

        try:
            parsed_response = json.loads(
                cleaned_response,
            )

        except json.JSONDecodeError:
            json_object = re.search(
                r"\{.*\}",
                cleaned_response,
                flags=re.DOTALL,
            )

            if json_object is None:
                raise LLMInvalidResponseError(
                    "The LLM planner did not return JSON."
                )

            try:
                parsed_response = json.loads(
                    json_object.group(0),
                )

            except json.JSONDecodeError as exception:
                raise LLMInvalidResponseError(
                    "The LLM planner returned malformed JSON."
                ) from exception

        if not isinstance(parsed_response, dict):
            raise LLMInvalidResponseError(
                "The LLM planner JSON must be an object."
            )

        return parsed_response

    @staticmethod
    def _normalize_text(
        value: str,
    ) -> str:
        normalized_value = value.casefold()

        normalized_value = re.sub(
            r"\s+",
            " ",
            normalized_value,
        )

        return normalized_value.strip()

    @staticmethod
    def _format_error(
        exception: Exception,
    ) -> str:
        exception_name = type(exception).__name__
        exception_message = str(exception).strip()

        if not exception_message:
            return exception_name

        return (
            f"{exception_name}: "
            f"{exception_message}"
        )[:1000]