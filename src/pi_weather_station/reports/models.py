from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class WeatherData:
    wind_dir: float = 0.0
    wind_spd: float = 0.0
    wind_gst: float = 0.0
    temp_amb: float = 0.0
    temp_gnd: float = 0.0
    pressure: float = 0.0
    humidity: float = 0.0
    rainfall: float = 0.0

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "WeatherData":
        return WeatherData(
            wind_dir=float(data.get("wind_dir", 0.0)),
            wind_spd=float(data.get("wind_spd", 0.0)),
            wind_gst=float(data.get("wind_gst", 0.0)),
            temp_amb=float(data.get("temp_amb", 0.0)),
            temp_gnd=float(data.get("temp_gnd", 0.0)),
            pressure=float(data.get("pressure", 0.0)),
            humidity=float(data.get("humidity", 0.0)),
            rainfall=float(data.get("rainfall", 0.0)),
        )

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class WeatherReport:
    station_id: str
    timestamp_utc: datetime
    data: WeatherData
    source: str = "local"

    @staticmethod
    def placeholder(station_id: str) -> "WeatherReport":
        return WeatherReport(
            station_id=station_id,
            timestamp_utc=datetime.now(timezone.utc),
            source="placeholder",
            data=WeatherData(),
        )

    @staticmethod
    def from_command_payload(payload: dict[str, Any], source: str) -> "WeatherReport":
        station_id = payload.get("stationId")
        if not station_id:
            raise ValueError("submit_report requires stationId")

        timestamp_raw = payload.get("timestampUtc")

        if timestamp_raw:
            timestamp = datetime.fromisoformat(
                str(timestamp_raw).replace("Z", "+00:00")
            )
        else:
            timestamp = datetime.now(timezone.utc)

        data_raw = payload.get("data")
        if not isinstance(data_raw, dict):
            raise ValueError("submit_report requires data object")

        return WeatherReport(
            station_id=str(station_id),
            timestamp_utc=timestamp,
            source=source,
            data=WeatherData.from_dict(data_raw),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "stationId": self.station_id,
            "timestampUtc": self.timestamp_utc.isoformat(),
            "source": self.source,
            "data": self.data.to_dict(),
        }