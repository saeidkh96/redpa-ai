from __future__ import annotations

import re
import unicodedata
from typing import Any


class ResearchEvidenceCleaner:
    """Normalize untrusted search-result text before ranking and prompting."""

    _REMOVABLE_PHRASES = (
        r"\bread more\b",
        r"\blearn more\b",
        r"\bsign in\b",
        r"\bsign up\b",
        r"\bsubscribe(?: now)?\b",
        r"\baccept all cookies\b",
        r"\bcookie preferences\b",
        r"\benable javascript\b",
        r"\badvertisement\b",
    )

    _INSTRUCTION_PATTERNS = (
        r"<\s*/?\s*(tool_call|function|assistant|system|developer|script)[^>]*>",
        r"\b(ignore|disregard|forget)\s+(all\s+)?(previous|prior)\s+instructions\b",
        r"\byou are now\b",
        r"\bsystem prompt\b",
    )

    @classmethod
    def clean(cls, value: Any, *, max_length: int = 1800) -> str:
        text = unicodedata.normalize("NFKC", str(value or ""))
        text = re.sub(r"<[^>]+>", " ", text)

        for pattern in cls._INSTRUCTION_PATTERNS:
            text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

        for pattern in cls._REMOVABLE_PHRASES:
            text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

        text = "".join(
            character
            for character in text
            if character in {"\n", "\t"}
            or unicodedata.category(character)[0] != "C"
        )
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()[:max_length]
