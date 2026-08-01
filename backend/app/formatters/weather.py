from __future__ import annotations

from typing import Any


def format_weather_result(
    result: dict[str, Any],
) -> str:
    location = result.get("location", {})

    if not isinstance(location, dict):
        location = {}

    location_parts = [
        str(value)
        for value in (
            location.get("name"),
            location.get("admin1"),
            location.get("country"),
        )
        if value
    ]

    location_label = (
        ", ".join(location_parts)
        or "Unknown location"
    )

    temperature = result.get("temperature")
    temperature_unit = result.get(
        "temperature_unit",
        "°C",
    )

    lines = [
        f"Current weather for {location_label}",
        "",
        f"Condition: {result.get('condition') or 'Unknown'}",
        f"Temperature: {temperature} {temperature_unit}",
    ]

    apparent_temperature = result.get(
        "apparent_temperature",
    )

    if apparent_temperature is not None:
        lines.append(
            "Feels like: "
            f"{apparent_temperature} {temperature_unit}"
        )

    humidity = result.get("humidity")

    if humidity is not None:
        lines.append(
            f"Humidity: {humidity} "
            f"{result.get('humidity_unit', '%')}"
        )

    wind_speed = result.get("wind_speed")

    if wind_speed is not None:
        lines.append(
            f"Wind: {wind_speed} "
            f"{result.get('wind_speed_unit', 'km/h')}"
        )

    precipitation = result.get("precipitation")

    if precipitation is not None:
        lines.append(
            f"Precipitation: {precipitation} "
            f"{result.get('precipitation_unit', 'mm')}"
        )

    observed_at = result.get("observed_at")

    if observed_at:
        lines.extend(
            [
                "",
                f"Observed at: {observed_at}",
            ]
        )

    provider = result.get("provider")

    if provider:
        lines.append(
            f"Provider: {provider}"
        )

    return "\n".join(lines)
