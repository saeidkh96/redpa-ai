from __future__ import annotations

from time import perf_counter
from typing import Any

from app.tools.http_base import BaseHTTPTool
from app.tools.schemas import ToolExecutionResult, ToolMetadata


WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
}


class WeatherTool(BaseHTTPTool):
    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="weather",
            description=(
                "Returns current weather for a city using Open-Meteo."
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
            location = self.required_string(
                arguments,
                "location",
                max_length=150,
            )

            geocoding = await self.http_client.get_json(
                url="https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": location,
                    "count": 1,
                    "language": "en",
                    "format": "json",
                },
                allowed_hosts={"open-meteo.com"},
            )

            results = (
                geocoding.data.get("results", [])
                if isinstance(geocoding.data, dict)
                else []
            )

            if not results:
                return self._failure(
                    started_at,
                    f"No location was found for '{location}'.",
                    "location_not_found",
                )

            place = results[0]
            latitude = float(place["latitude"])
            longitude = float(place["longitude"])
            timezone = str(place.get("timezone") or "auto")

            weather = await self.http_client.get_json(
                url="https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": (
                        "temperature_2m,relative_humidity_2m,"
                        "apparent_temperature,precipitation,"
                        "weather_code,wind_speed_10m"
                    ),
                    "timezone": timezone,
                },
                allowed_hosts={"open-meteo.com"},
            )

            if not isinstance(weather.data, dict):
                return self._failure(
                    started_at,
                    "Open-Meteo returned an invalid response.",
                    "invalid_response",
                )

            current = weather.data.get("current")
            units = weather.data.get("current_units", {})

            if not isinstance(current, dict):
                return self._failure(
                    started_at,
                    "Open-Meteo returned no current weather.",
                    "missing_current_weather",
                )

            code = int(current.get("weather_code", -1))

            result = {
                "location": {
                    "name": place.get("name"),
                    "country": place.get("country"),
                    "admin1": place.get("admin1"),
                    "latitude": latitude,
                    "longitude": longitude,
                    "timezone": timezone,
                },
                "observed_at": current.get("time"),
                "condition": WEATHER_CODES.get(
                    code,
                    f"Weather code {code}",
                ),
                "temperature": current.get("temperature_2m"),
                "temperature_unit": units.get("temperature_2m", "°C"),
                "apparent_temperature": current.get(
                    "apparent_temperature"
                ),
                "humidity": current.get("relative_humidity_2m"),
                "humidity_unit": units.get(
                    "relative_humidity_2m",
                    "%",
                ),
                "precipitation": current.get("precipitation"),
                "precipitation_unit": units.get(
                    "precipitation",
                    "mm",
                ),
                "wind_speed": current.get("wind_speed_10m"),
                "wind_speed_unit": units.get(
                    "wind_speed_10m",
                    "km/h",
                ),
                "provider": "Open-Meteo",
            }

            return ToolExecutionResult(
                tool_name=self.metadata.name,
                success=True,
                result=result,
                error=None,
                execution_time_ms=self._elapsed_ms(started_at),
                metadata={
                    "provider": "open-meteo",
                    "location_query": location,
                },
            )

        except Exception as exception:
            return self._failure(
                started_at,
                f"{type(exception).__name__}: {exception}",
                type(exception).__name__,
            )

    def _failure(
        self,
        started_at: float,
        error: str,
        error_type: str,
    ) -> ToolExecutionResult:
        return ToolExecutionResult(
            tool_name=self.metadata.name,
            success=False,
            result=None,
            error=error[:1000],
            execution_time_ms=self._elapsed_ms(started_at),
            metadata={"error_type": error_type},
        )

    @staticmethod
    def _elapsed_ms(started_at: float) -> float:
        return round((perf_counter() - started_at) * 1000, 2)
