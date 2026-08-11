from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class ContentGuardrailDecision(StrEnum):
    ALLOW = "allow"
    REDACT = "redact"
    REVIEW = "review"
    BLOCK = "block"


@dataclass(frozen=True, slots=True)
class ContentGuardrailResult:
    decision: ContentGuardrailDecision
    content: str
    reasons: tuple[str, ...] = ()


class ProductionGuardrailPipeline:
    _email = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
    _secret = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b")
    _injection = re.compile(r"(?:ignore|disregard).{0,30}(?:previous|system|developer).{0,30}(?:instruction|prompt)", re.I)

    def evaluate_input(self, content: str) -> ContentGuardrailResult:
        if self._injection.search(content):
            return ContentGuardrailResult(ContentGuardrailDecision.REVIEW, content, ("prompt_injection_pattern",))
        reasons: list[str] = []
        redacted = content
        if self._secret.search(redacted):
            redacted = self._secret.sub("[REDACTED_SECRET]", redacted)
            reasons.append("secret_redacted")
        if self._email.search(redacted):
            redacted = self._email.sub("[REDACTED_EMAIL]", redacted)
            reasons.append("email_redacted")
        return ContentGuardrailResult(ContentGuardrailDecision.REDACT if reasons else ContentGuardrailDecision.ALLOW, redacted, tuple(reasons))

    def evaluate_output(self, content: str) -> ContentGuardrailResult:
        reasons: list[str] = []
        redacted = content
        if self._secret.search(redacted):
            redacted = self._secret.sub("[REDACTED_SECRET]", redacted)
            reasons.append("secret_redacted")
        if self._email.search(redacted):
            redacted = self._email.sub("[REDACTED_EMAIL]", redacted)
            reasons.append("email_redacted")
        return ContentGuardrailResult(ContentGuardrailDecision.REDACT if reasons else ContentGuardrailDecision.ALLOW, redacted, tuple(reasons))
