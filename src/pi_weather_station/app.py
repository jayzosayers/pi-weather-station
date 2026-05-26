import asyncio
from datetime import datetime, timezone

from pi_weather_station.api.api_client import ApiClient
from pi_weather_station.api.uploader import ReportUploader
from pi_weather_station.commands.command_bus import Command, CommandBus
from pi_weather_station.commands.handlers import CommandHandlers
from pi_weather_station.commands.parser import parse_command_text
from pi_weather_station.comms.local_command_server import LocalCommandServer
from pi_weather_station.comms.serial_discovery import discover_usb_serial_devices
from pi_weather_station.comms.serial_radio import SerialRadioConfig, SerialRadioListener
from pi_weather_station.config import AppConfig
from pi_weather_station.reports.report_cache import ReportCache
from pi_weather_station.reports.upload_queue import UploadQueue
from pi_weather_station.sensors.measurement_service import MeasurementService


class App:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._stop_event = asyncio.Event()
        self._tasks: list[asyncio.Task] = []

        self.command_bus = CommandBus()
        self.local_command_server = LocalCommandServer(self.command_bus)

        self.report_cache = ReportCache()
        self.upload_queue = UploadQueue(max_size=256)
        self.command_handlers = CommandHandlers(
            config,
            self.report_cache,
            self.upload_queue,
        )
        
        self.api_client = ApiClient(config)
        self.report_uploader = ReportUploader(self.api_client, self.upload_queue)

        self.command_bus.register("status", self.command_handlers.status)
        self.command_bus.register(
            "get_latest_report",
            self.command_handlers.get_latest_report,
        )
        self.command_bus.register("submit_report", self.command_handlers.submit_report)
        
        self.measurement_service = MeasurementService(
            config,
            self.report_cache,
            self.upload_queue,
        )

    async def initialize(self) -> None:
        pass

    async def run(self) -> None:
        print(
            f"pi-weather-station starting for station {self.config.station_id} "
            f"in {self.config.mode} mode",
            flush=True,
        )

        await self.initialize()
        await self._run_startup_tests()

        task = asyncio.create_task(self.local_command_server.start())
        self._tasks.append(task)
        
        task = asyncio.create_task(self.report_uploader.run())
        self._tasks.append(task)
        
        task = asyncio.create_task(self.measurement_service.run())
        self._tasks.append(task)
        
        await self._start_serial_listeners()

        try:
            while not self._stop_event.is_set():
                # MAIN PROGRAM LOOP
                now = datetime.now(timezone.utc).isoformat()
                print(
                    f"[{now}] {self.config.station_id}: Loop Executed",
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