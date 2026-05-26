from datetime import datetime, timezone

from pi_weather_station.commands.command_bus import Command, CommandResponse
from pi_weather_station.config import AppConfig
from pi_weather_station.reports.models import WeatherReport
from pi_weather_station.reports.report_cache import ReportCache
from pi_weather_station.reports.upload_queue import UploadQueue

class CommandHandlers:
    def __init__(
        self,
        config: AppConfig,
        report_cache: ReportCache,
        upload_queue: UploadQueue,
    ) -> None:
        self.config = config
        self.report_cache = report_cache
        self.upload_queue = upload_queue

    def status(self, command: Command) -> CommandResponse:
        return CommandResponse(
            ok=True,
            message="Station online",
            data={
                "stationId": self.config.station_id,
                "mode": self.config.mode,
                "source": command.source,
                "timeUtc": datetime.now(timezone.utc).isoformat(),
            },
        )

    async def get_latest_report(self, command: Command) -> CommandResponse:
        station_id = command.payload.get("stationId", self.config.station_id)

        report = await self.report_cache.get_latest(station_id)

        if report is None:
            return CommandResponse(
                ok=False,
                message=f"No weather report available for {station_id}",
                data={"stationId": station_id},
            )

        return CommandResponse(
            ok=True,
            message=f"Latest report for {station_id}",
            data=report.to_dict(),
        )

    async def submit_report(self, command: Command) -> CommandResponse:
        report = WeatherReport.from_command_payload(
            command.payload,
            source=command.source,
        )

        await self.report_cache.store(report)
        await self.upload_queue.enqueue(report)

        return CommandResponse(
            ok=True,
            message=f"Stored report for {report.station_id}",
            data=report.to_dict(),
        )