from __future__ import annotations

import asyncio

from pi_weather_station.reports.models import WeatherReport


class ReportCache:
    def __init__(self) -> None:
        self._latest_by_station_id: dict[str, WeatherReport] = {}
        self._lock = asyncio.Lock()

    async def store(self, report: WeatherReport) -> None:
        async with self._lock:
            self._latest_by_station_id[report.station_id] = report

    async def get_latest(self, station_id: str) -> WeatherReport | None:
        async with self._lock:
            return self._latest_by_station_id.get(station_id)

    async def get_all_latest(self) -> list[WeatherReport]:
        async with self._lock:
            return list(self._latest_by_station_id.values())