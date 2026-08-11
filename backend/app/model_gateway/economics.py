from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelEconomics:
    provider: str
    model: str
    input_per_1k: float = 0.0
    output_per_1k: float = 0.0
    quality_tier: int = 1
    latency_tier: int = 1
    pricing_known: bool = True

    def estimate(
        self,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        if not self.pricing_known:
            return math.inf

        return (
            max(input_tokens, 0) / 1000 * self.input_per_1k
            + max(output_tokens, 0) / 1000 * self.output_per_1k
        )


class ModelEconomicsCatalog:
    def __init__(
        self,
        entries: dict[str, ModelEconomics] | None = None,
    ) -> None:
        self.entries = entries or {}

    @classmethod
    def from_environment(
        cls,
    ) -> "ModelEconomicsCatalog":
        raw = os.getenv(
            "MODEL_GATEWAY_ECONOMICS_JSON",
            "",
        ).strip()

        if not raw:
            return cls()

        payload = json.loads(raw)

        entries: dict[str, ModelEconomics] = {}

        for key, value in payload.items():
            if not isinstance(value, dict):
                continue

            provider, _, model = str(key).partition(":")

            entries[key] = ModelEconomics(
                provider=provider,
                model=model or "*",
                input_per_1k=float(
                    value.get(
                        "input_per_1k",
                        0.0,
                    )
                ),
                output_per_1k=float(
                    value.get(
                        "output_per_1k",
                        0.0,
                    )
                ),
                quality_tier=int(
                    value.get(
                        "quality_tier",
                        1,
                    )
                ),
                latency_tier=int(
                    value.get(
                        "latency_tier",
                        1,
                    )
                ),
                pricing_known=True,
            )

        return cls(entries)

    def get(
        self,
        provider: str,
        model: str,
    ) -> ModelEconomics:
        direct = self.entries.get(
            f"{provider}:{model}"
        )

        if direct is not None:
            return direct

        wildcard = self.entries.get(
            f"{provider}:*"
        )

        if wildcard is not None:
            return wildcard

        return ModelEconomics(
            provider=provider,
            model=model,
            pricing_known=False,
        )