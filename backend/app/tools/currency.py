from __future__ import annotations

from decimal import Decimal, InvalidOperation
from time import perf_counter
from typing import Any

from app.tools.http_base import BaseHTTPTool
from app.tools.schemas import ToolExecutionResult, ToolMetadata


class CurrencyTool(BaseHTTPTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="currency",
            description=(
                "Converts an amount between currencies using "
                "Frankfurter reference exchange rates."
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
            source = self.required_string(
                arguments,
                "from_currency",
                max_length=3,
            ).upper()
            target = self.required_string(
                arguments,
                "to_currency",
                max_length=3,
            ).upper()

            try:
                amount = Decimal(
                    str(arguments.get("amount", ""))
                )
            except InvalidOperation as exception:
                raise ValueError(
                    "'amount' must be a valid number."
                ) from exception

            if amount <= 0 or amount > Decimal("1000000000"):
                raise ValueError(
                    "'amount' must be greater than zero and reasonable."
                )

            if source == target:
                result = {
                    "date": None,
                    "amount": float(amount),
                    "from_currency": source,
                    "to_currency": target,
                    "rate": 1.0,
                    "converted_amount": float(amount),
                    "provider": "Frankfurter",
                }
            else:
                response = await self.http_client.get_json(
                    url="https://api.frankfurter.dev/v1/latest",
                    params={
                        "base": source,
                        "symbols": target,
                    },
                    allowed_hosts={"frankfurter.dev"},
                )

                if not isinstance(response.data, dict):
                    raise ValueError(
                        "Frankfurter returned an invalid response."
                    )

                rates = response.data.get("rates", {})
                rate_value = rates.get(target)

                if rate_value is None:
                    raise ValueError(
                        f"No exchange rate is available for {source}/{target}."
                    )

                rate = Decimal(str(rate_value))
                converted = amount * rate

                result = {
                    "date": response.data.get("date"),
                    "amount": float(amount),
                    "from_currency": source,
                    "to_currency": target,
                    "rate": float(rate),
                    "converted_amount": float(
                        converted.quantize(Decimal("0.0001"))
                    ),
                    "provider": "Frankfurter",
                }

            return ToolExecutionResult(
                tool_name=self.metadata.name,
                success=True,
                result=result,
                error=None,
                execution_time_ms=self._elapsed_ms(started_at),
                metadata={"provider": "frankfurter"},
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
