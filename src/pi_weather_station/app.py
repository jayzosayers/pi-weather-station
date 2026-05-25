import asyncio
from datetime import datetime, timezone

from pi_weather_station.commands.command_bus import Command, CommandBus
from pi_weather_station.commands.handlers import CommandHandlers
from pi_weather_station.commands.parser import parse_command_text
from pi_weather_station.comms.serial_discovery import discover_usb_serial_devices
from pi_weather_station.comms.serial_radio import SerialRadioConfig, SerialRadioListener
from pi_weather_station.config import AppConfig


class App:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._stop_event = asyncio.Event()
        self._tasks: list[asyncio.Task] = []

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

        await self._run_startup_tests()
        await self._start_serial_listeners()

        try:
            while not self._stop_event.is_set():
                now = datetime.now(timezone.utc).isoformat()
                print(
                    f"[{now}] {self.config.station_id}: app running",
                    flush=True,
                )
                await asyncio.sleep(60)
        finally:
            await self._stop_background_tasks()

    def stop(self) -> None:
        self._stop_event.set()

    async def _run_startup_tests(self) -> None:
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

    async def _start_serial_listeners(self) -> None:
        devices = discover_usb_serial_devices()

        if not devices:
            print("No USB serial devices discovered", flush=True)
            return

        print(f"Discovered {len(devices)} USB serial device(s)", flush=True)

        for device in devices:
            print(
                f"USB serial device: {device.device} "
                f"{device.description} {device.hwid}",
                flush=True,
            )

            listener = SerialRadioListener(
                device=device,
                command_bus=self.command_bus,
                config=SerialRadioConfig(baud_rate=115200),
            )

            task = asyncio.create_task(listener.run())
            self._tasks.append(task)

    async def _stop_background_tasks(self) -> None:
        if not self._tasks:
            return

        print("Stopping background tasks", flush=True)

        for task in self._tasks:
            task.cancel()

        await asyncio.gather(*self._tasks, return_exceptions=True)