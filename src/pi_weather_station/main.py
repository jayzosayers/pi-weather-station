import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path


async def run(config_path: Path) -> None:
    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    station_id = config.get("stationId", "UNKNOWN")
    print(f"pi-weather-station starting for station {station_id}", flush=True)

    while True:
        now = datetime.now(timezone.utc).isoformat()
        print(f"[{now}] {station_id}: hello from pi-weather-station", flush=True)
        await asyncio.sleep(60)


def main() -> None:
    parser = argparse.ArgumentParser(prog="pi-weather-station")
    parser.add_argument("--config", default="/boot/firmware/pi-weather-station.json")
    args = parser.parse_args()

    asyncio.run(run(Path(args.config)))