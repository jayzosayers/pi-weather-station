import json
import shlex
from typing import Any

from pi_weather_station.commands.command_bus import Command


REPORT_COMMANDS = {
    "report",
    "weather-report",
    "weather_report",
    "latest",
    "latest-report",
}

STATUS_COMMANDS = {
    "status",
    "ping",
}


def parse_command_text(text: str, source: str = "unknown") -> Command:
    text = text.strip()

    if not text:
        raise ValueError("Empty command")

    if text.startswith("{"):
        return _parse_json_command(text, source)

    return _parse_human_command(text, source)


def _parse_json_command(text: str, source: str) -> Command:
    data: dict[str, Any] = json.loads(text)

    command_type = data.get("type")
    if not isinstance(command_type, str) or not command_type:
        raise ValueError("JSON command must include a string 'type' field")

    payload = {k: v for k, v in data.items() if k != "type"}

    return Command(
        type=command_type,
        payload=payload,
        source=source,
    )


def _parse_human_command(text: str, source: str) -> Command:
    parts = shlex.split(text)

    if not parts:
        raise ValueError("Empty command")

    command_name = parts[0].lower()

    if command_name in STATUS_COMMANDS:
        return Command(type="status", payload={}, source=source)

    if command_name in REPORT_COMMANDS:
        if len(parts) < 2:
            raise ValueError("Usage: report <station-id>")

        return Command(
            type="get_latest_report",
            payload={"stationId": parts[1]},
            source=source,
        )

    raise ValueError(f"Unknown command: {command_name}")