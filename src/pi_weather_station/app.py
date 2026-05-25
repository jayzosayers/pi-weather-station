import asyncio
from datetime import datetime, timezone

from pi_weather_station.commands.command_bus import Command, CommandBus
from pi_weather_station.commands.handlers import CommandHandlers
from pi_weather_station.commands.parser import parse_command_text
from pi_weather_station.config import AppConfig


class App:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._stop_event = asyncio.Event()

        self.command_bus = CommandBus()
        self.command_handlers = CommandHandlers(config)

        self.command_bus.register("status", self.command_handlers.status)
        self.command_bus.register(
            "get_latest_report",
            self.command_handlers.get_latest_report,
        )

    async def run(self) -> None:
        print(
            f"pi-weather-station starting for station {self.config.station_id} "
            f"in {self.config.mode} mode",
            flush=True,
        )

        response = await self.command_bus.dispatch(
            Command(type="status", payload={}, source="startup")
        )
        print(f"Startup status: {response}", flush=True)

        try:
            test_command = parse_command_text(
                f"weather-report {self.config.station_id}",
                source="startup-test",
            )
            response = await self.command_bus.dispatch(test_command)
            print(f"Startup command test: {response}", flush=True)
        except Exception as exc:
            print(f"Startup command test failed: {exc}", flush=True)

        while not self._stop_event.is_set():
            now = datetime.now(timezone.utc).isoformat()
            print(
                f"[{now}] {self.config.station_id}: app running",
                flush=True,
            )
            await asyncio.sleep(60)

    def stop(self) -> None:
        self._stop_event.set()