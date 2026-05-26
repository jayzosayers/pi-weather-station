from datetime import datetime, timezone

from pi_weather_station.config import AppConfig
from pi_weather_station.reports.models import WeatherReport
from pi_weather_station.reports.report_cache import ReportCache
from pi_weather_station.reports.upload_queue import UploadQueue
from pi_weather_station.sensors.weather_measurement import (
    MeasurementConfig,
    WeatherMeasurement,
)


class MeasurementService:
    def __init__(
        self,
        config: AppConfig,
        report_cache: ReportCache,
        upload_queue: UploadQueue,
    ) -> None:
        self.config = config
        self.report_cache = report_cache
        self.upload_queue = upload_queue
        self.measurement = WeatherMeasurement(MeasurementConfig())
        self._stopped = False

    async def run(self) -> None:
        print("Measurement service started", flush=True)

        while not self._stopped:
            try:
                data = await self.measurement.measure_once()

                report = WeatherReport(
                    station_id=self.config.station_id,
                    timestamp_utc=datetime.now(timezone.utc),
                    source="local-sensors",
                    data=data,
                )

                await self.report_cache.store(report)
                await self.upload_queue.enqueue(report)

                print(f"Measured report: {report.to_dict()}", flush=True)

            except Exception as exc:
                print(f"Measurement failed: {exc}", flush=True)

    def stop(self) -> None:
        self._stopped = True