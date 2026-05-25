import argparse
import asyncio
from pathlib import Path

from pi_weather_station.app import App
from pi_weather_station.commands.parser import parse_command_text
from pi_weather_station.config import load_config


async def run_cli_command(config_path: Path, command_parts: list[str]) -> None:
    config = load_config(config_path)
    app = App(config)

    command_text = " ".join(command_parts)
    command = parse_command_text(command_text, source="cli")

    response = await app.command_bus.dispatch(command)
    print(response)


def main() -> None:
    parser = argparse.ArgumentParser(prog="pi-weather-station")
    parser.add_argument("--config", default="/boot/firmware/pi-weather-station.json")
    parser.add_argument(
        "command_parts",
        nargs="*",
        help="Optional command, e.g. 'status' or 'report STATION_ID'",
    )

    args = parser.parse_args()
    config_path = Path(args.config)

    if args.command_parts:
        asyncio.run(run_cli_command(config_path, args.command_parts))
        return

    config = load_config(config_path)
    app = App(config)
    asyncio.run(app.run())