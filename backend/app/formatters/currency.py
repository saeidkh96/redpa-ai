from __future__ import annotations

from typing import Any


def format_currency_result(
    result: dict[str, Any],
) -> str:
    amount = result.get("amount")
    source = result.get("from_currency")
    target = result.get("to_currency")
    converted = result.get("converted_amount")
    rate = result.get("rate")
    rate_date = result.get("date")
    provider = result.get("provider")

    lines = [
        "Currency conversion",
        "",
        f"{amount} {source} = {converted} {target}",
        f"Reference rate: 1 {source} = {rate} {target}",
    ]

    if rate_date:
        lines.append(
            f"Rate date: {rate_date}"
        )

    if provider:
        lines.append(
            f"Provider: {provider}"
        )

    return "\n".join(lines)
