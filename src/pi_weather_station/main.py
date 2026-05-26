import argparse
import asyncio
import json
from pathlib import Path

from pi_weather_station.app import App
from pi_weather_station.config import load_config


DEFAULT_COMMAND_HOST = "127.0.0.1"
DEFAULT_COMMAND_PORT = 8765


async def send_command_to_daemon(
    command_parts: list[str],
    host: str = DEFAULT_COMMAND_HOST,
    port: int = DEFAULT_COMMAND_PORT,
) -> None:
    command_text = " ".join(command_parts)

    reader, writer = await asyncio.open_connection(host, port)

    writer.write((command_text + "\n").encode("utf-8"))
    await writer.drain()

    response_raw = await reader.readline()

    writer.close()
    await writer.wait_closed()

    response_text = response_raw.decode("utf-8", errors="replace").strip()

    try:
        response = json.loads(response_text)
        print(json.dumps(response, indent=2))
    except json.JSONDecodeError:
        print(response_text)


async def run_daemon(config_path: Path) -> None:
    config = load_config(config_path)
    app = App(config)
    await app.run()


def main() -> None:
    parser = argparse.ArgumentParser(prog="pi-weather-station")
    parser.add_argument("--config", default="/boot/firmware/pi-weather-station.json")
    parser.add_argument("--host", default=DEFAULT_COMMAND_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_COMMAND_PORT)
    parser.add_argument(
        "command_parts",
        nargs="*",
        help="Optional command, e.g. 'status' or 'report STATION_ID'",
    )

    args = parser.parse_args()
    config_path = Path(args.config)

    if args.command_parts:
        asyncio.run(
            send_command_to_daemon(
                args.command_parts,
                host=args.host,
                port=args.port,
            )
        )
        return

    asyncio.run(run_daemon(config_path))