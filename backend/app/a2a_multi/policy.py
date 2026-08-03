from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class A2AApprovalDecision:
    required: bool
    reason: str | None
    matched_signal: str | None


class A2AApprovalPolicy:
    HIGH_RISK_PATTERNS: tuple[tuple[str, str], ...] = (
        (
            r"\bsend\s+(an?\s+)?email\b",
            "Sending an email is an external side effect.",
        ),
        (
            r"\b(delete|remove|drop|truncate)\b",
            "The request may delete or remove data.",
        ),
        (
            r"\b(restart|stop|kill)\s+(a\s+)?(container|service)\b",
            "The request may modify infrastructure state.",
        ),
        (
            r"\b(create|update|modify|write)\b.*\b(database|file|record)\b",
            "The request may modify persistent data.",
        ),
        (
            r"\b(issue|process)\s+(a\s+)?refund\b",
            "The request may trigger a financial action.",
        ),
        (
            r"\bpublish|deploy\s+to\s+production\b",
            "The request may change a production environment.",
        ),
    )

    @classmethod
    def evaluate(
        cls,
        request: str,
    ) -> A2AApprovalDecision:
        normalized = str(
            request
            or "",
        ).casefold()

        for pattern, reason in cls.HIGH_RISK_PATTERNS:
            match = re.search(
                pattern,
                normalized,
                flags=re.IGNORECASE,
            )

            if match is not None:
                return A2AApprovalDecision(
                    required=True,
                    reason=reason,
                    matched_signal=match.group(0),
                )

        return A2AApprovalDecision(
            required=False,
            reason=None,
            matched_signal=None,
        )
