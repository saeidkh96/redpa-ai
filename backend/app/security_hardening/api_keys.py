from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GeneratedAPIKey:
    key_id: str
    raw_key: str
    key_hash: str


class APIKeyService:
    PREFIX = "redpa"

    @classmethod
    def generate(
        cls,
    ) -> GeneratedAPIKey:
        key_id = secrets.token_hex(
            8,
        )

        secret = secrets.token_urlsafe(
            32,
        )

        raw_key = (
            f"{cls.PREFIX}_{key_id}_{secret}"
        )

        return GeneratedAPIKey(
            key_id=key_id,
            raw_key=raw_key,
            key_hash=cls.hash_key(
                raw_key,
            ),
        )

    @staticmethod
    def hash_key(
        raw_key: str,
    ) -> str:
        pepper = os.getenv(
            "API_KEY_PEPPER",
            "",
        ).encode(
            "utf-8",
        )

        return hmac.new(
            pepper,
            raw_key.encode(
                "utf-8",
            ),
            hashlib.sha256,
        ).hexdigest()

    @classmethod
    def verify(
        cls,
        raw_key: str,
        expected_hash: str,
    ) -> bool:
        return hmac.compare_digest(
            cls.hash_key(
                raw_key,
            ),
            expected_hash,
        )
